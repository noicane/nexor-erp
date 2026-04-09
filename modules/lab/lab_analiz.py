# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Banyo Analiz Sonuçları (KATAFOREZ PARAMETRELERİ İLE)
uretim.banyo_analiz_sonuclari tablosu için CRUD
Versiyon: 2.0 - Kataforez Modülü
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QDoubleSpinBox, QTextEdit, QComboBox, QDateTimeEdit, QTabWidget, QWidget, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from datetime import datetime


def gonder_lab_whatsapp_bildirimi(banyo_id, durum, params):
    """WhatsApp bildirimi gönder - Standalone fonksiyon"""
    print(f"WhatsApp gonderimi baslatiliyor... (Banyo: {banyo_id}, Durum: {durum})")

    alicilar = []
    banyo_adi = f"Banyo-{banyo_id}"
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # WhatsApp abonesi kullanıcıları bul
        cursor.execute("""
            SELECT k.id, k.telefon, k.ad, k.soyad
            FROM sistem.kullanicilar k
            JOIN sistem.bildirim_abonelikleri a ON k.id = a.kullanici_id
            WHERE a.whatsapp_bildirim = 1
              AND k.aktif_mi = 1
              AND k.telefon IS NOT NULL
        """)

        alicilar = cursor.fetchall()
        print(f"Bulunan abone sayisi: {len(alicilar)}")

        if not alicilar:
            print("WhatsApp abonesi bulunamadi")
            return

        # Banyo bilgisini al
        cursor.execute("SELECT kod, ad FROM uretim.banyo_tanimlari WHERE id = ?", (banyo_id,))
        banyo_bilgi = cursor.fetchone()
        banyo_adi = f"{banyo_bilgi[0]} - {banyo_bilgi[1]}" if banyo_bilgi else f"Banyo-{banyo_id}"

    except Exception as e:
        print(f"WhatsApp bildirim DB hatasi: {e}")
        return
    finally:
        if conn:
            try: conn.close()
            except Exception: pass

    # Mesaj sablonu
    try:
        emoji = "🔴" if durum == "KRITIK" else "⚠️"
        mesaj = f"""{emoji} NEXOR ERP - Lab Analiz {durum}!

🧪 Banyo: {banyo_adi}
🌡️ Sıcaklık: {params[3]:.1f}°C
⚗️ pH: {params[4]:.2f}
📅 Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}

Lütfen kontrol edin!"""

        from utils.whatsapp_service import gonder_whatsapp

        basarili = 0
        for kullanici_id, telefon, ad, soyad in alicilar:
            success, msg = gonder_whatsapp(telefon, mesaj)
            if success:
                basarili += 1
                print(f"WhatsApp gonderildi: {ad} {soyad} ({telefon})")
            else:
                print(f"WhatsApp gonderilemedi: {ad} {soyad} - {msg}")

        print(f"WhatsApp bildirimi: {basarili}/{len(alicilar)} basarili")

    except ImportError as ie:
        print(f"WhatsApp servisi bulunamadi: {ie}")
    except Exception as e:
        print(f"WhatsApp bildirim hatasi: {e}")
        import traceback
        traceback.print_exc()


class AnalizDialog(QDialog):
    """Analiz Sonucu Ekleme/Düzenleme - KATAFOREZ PARAMETRELERİ İLE"""
    
    def __init__(self, theme: dict, analiz_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.analiz_id = analiz_id
        self.data = {}
        self.banyo_limitleri = {}
        self.tds_parametreler = []
        self.tds_id = None

        self.setWindowTitle("Yeni Kataforez Analiz" if not analiz_id else "Kataforez Analiz Düzenle")
        self.setMinimumSize(850, 800)
        
        if analiz_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_analiz_sonuclari WHERE id = ?", (self.analiz_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QTextEdit, QDoubleSpinBox, QComboBox, QDateTimeEdit {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
            QTabWidget::pane {{ 
                border: 1px solid {self.theme['border']}; 
                background: {self.theme['bg_card_solid']}; 
                border-radius: 8px;
            }}
            QTabBar::tab {{ 
                background: {self.theme['bg_input']}; 
                padding: 10px 20px; 
                color: {self.theme['text']};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{ 
                background: {self.theme['bg_card_solid']}; 
                border-bottom: 3px solid {self.theme['primary']}; 
            }}
            QGroupBox {{
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                background: {self.theme['bg_card_solid']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {self.theme['primary']};
                font-weight: bold;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Başlık
        title = QLabel("🧪 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        # Temel Bilgiler
        temel_form = QFormLayout()
        temel_form.setSpacing(10)
        
        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("-- Seçiniz --", None)
        self._load_banyolar()
        self.banyo_combo.currentIndexChanged.connect(self._on_banyo_changed)
        temel_form.addRow("Banyo *:", self.banyo_combo)
        
        self.tarih_input = QDateTimeEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        if self.data.get('tarih'):
            self.tarih_input.setDateTime(self.data['tarih'])
        else:
            self.tarih_input.setDateTime(QDateTime.currentDateTime())
        temel_form.addRow("Tarih *:", self.tarih_input)
        
        self.analist_combo = QComboBox()
        self.analist_combo.addItem("-- Seçiniz --", None)
        self._load_analistler()
        temel_form.addRow("Analist *:", self.analist_combo)
        
        layout.addLayout(temel_form)
        
        # Parametreler - Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_temel_tab(), "Temel Parametreler")
        tabs.addTab(self._create_kataforez_tab(), "Kataforez Parametreleri")
        tabs.addTab(self._create_tds_ai_tab(), "TDS AI Degerlendirme")
        tabs.addTab(self._create_notlar_tab(), "Notlar")
        layout.addWidget(tabs, 1)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['bg_input']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 10px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {self.theme['border']};
            }}
        """)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['primary']};
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def _create_temel_tab(self):
        """Temel parametreler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Sıcaklık ve pH Group
        sic_ph_group = QGroupBox("🌡️ Sıcaklık ve pH")
        sic_ph_form = QFormLayout(sic_ph_group)
        
        self.sicaklik_input = self._create_param_spinbox(0, 200, " °C", self.data.get('sicaklik', 0))
        sic_ph_form.addRow("Sıcaklık:", self.sicaklik_input)
        
        self.ph_input = self._create_param_spinbox(0, 14, "", self.data.get('ph', 0), decimals=2)
        sic_ph_form.addRow("pH:", self.ph_input)
        
        layout.addWidget(sic_ph_group)
        
        # İletkenlik ve Asitlik Group
        ilet_asit_group = QGroupBox("⚡ İletkenlik ve Asitlik")
        ilet_asit_form = QFormLayout(ilet_asit_group)
        
        self.iletkenlik_input = self._create_param_spinbox(0, 99999, " µS/cm", self.data.get('iletkenlik', 0))
        ilet_asit_form.addRow("İletkenlik:", self.iletkenlik_input)
        
        self.toplam_asit_input = self._create_param_spinbox(0, 999, "", self.data.get('toplam_asitlik', 0), decimals=2)
        ilet_asit_form.addRow("Toplam Asitlik:", self.toplam_asit_input)
        
        self.serbest_asit_input = self._create_param_spinbox(0, 999, "", self.data.get('serbest_asitlik', 0), decimals=2)
        ilet_asit_form.addRow("Serbest Asitlik:", self.serbest_asit_input)
        
        layout.addWidget(ilet_asit_group)
        
        # Metal İçerikleri Group
        metal_group = QGroupBox("🔬 Metal İçerikleri")
        metal_form = QFormLayout(metal_group)
        
        self.demir_input = self._create_param_spinbox(0, 9999, " ppm", self.data.get('demir_ppm', 0), decimals=4)
        metal_form.addRow("Demir (Fe):", self.demir_input)
        
        self.cinko_input = self._create_param_spinbox(0, 9999, " ppm", self.data.get('cinko_ppm', 0), decimals=4)
        metal_form.addRow("Çinko (Zn):", self.cinko_input)
        
        layout.addWidget(metal_group)
        layout.addStretch()
        
        return widget
    
    def _create_kataforez_tab(self):
        """Kataforez özel parametreleri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Katı Madde Group
        kati_group = QGroupBox("📊 Katı Madde Ölçümü")
        kati_form = QFormLayout(kati_group)
        
        self.kati_madde_input = self._create_param_spinbox(0, 100, " %", self.data.get('kati_madde_yuzde', 0), decimals=2)
        kati_form.addRow("Katı Madde:", self.kati_madde_input)
        
        kati_info = QLabel("💡 İdeal: 15.0 - 20.0 % (Gravimetrik, 110°C, 3 saat)")
        kati_info.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 11px; font-style: italic;")
        kati_form.addRow("", kati_info)
        
        layout.addWidget(kati_group)
        
        # P/B Oranı Group
        pb_group = QGroupBox("🎨 Pigment / Bağlayıcı Oranı")
        pb_form = QFormLayout(pb_group)
        
        self.pb_orani_input = self._create_param_spinbox(0, 10, "", self.data.get('pb_orani', 0), decimals=2)
        pb_form.addRow("P/B Oranı:", self.pb_orani_input)
        
        pb_info = QLabel("💡 İdeal: 0.15 - 0.40 (Kül testi, 450-500°C)")
        pb_info.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 11px; font-style: italic;")
        pb_form.addRow("", pb_info)
        
        layout.addWidget(pb_group)
        
        # Solvent Group
        solvent_group = QGroupBox("💧 Solvent İçeriği")
        solvent_form = QFormLayout(solvent_group)
        
        self.solvent_input = self._create_param_spinbox(0, 100, " %", self.data.get('solvent_yuzde', 0), decimals=2)
        solvent_form.addRow("Solvent:", self.solvent_input)
        
        solvent_info = QLabel("💡 İdeal: 1.0 - 3.0 % (GC Analizi)")
        solvent_info.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 11px; font-style: italic;")
        solvent_form.addRow("", solvent_info)
        
        layout.addWidget(solvent_group)
        
        # MEQ Group
        meq_group = QGroupBox("⚗️ MEQ Değeri")
        meq_form = QFormLayout(meq_group)
        
        self.meq_input = self._create_param_spinbox(0, 999, " meq", self.data.get('meq_degeri', 0), decimals=2)
        meq_form.addRow("MEQ:", self.meq_input)
        
        meq_info = QLabel("💡 İdeal: 30 - 40 meq (Titrasyon)")
        meq_info.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 11px; font-style: italic;")
        meq_form.addRow("", meq_info)
        
        layout.addWidget(meq_group)
        layout.addStretch()
        
        return widget
    
    def _create_tds_ai_tab(self):
        """TDS AI Degerlendirme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # TDS bilgi satiri
        info_bar = QHBoxLayout()
        self.tds_info_label = QLabel("Banyo seciniz - TDS bilgileri otomatik yuklenecek")
        self.tds_info_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px;")
        info_bar.addWidget(self.tds_info_label)
        info_bar.addStretch()

        self.tds_analiz_btn = QPushButton("AI Analiz Baslat")
        self.tds_analiz_btn.setStyleSheet(
            "background: #7C3AED; color: white; border: none; "
            "padding: 6px 14px; border-radius: 4px; font-weight: bold;")
        self.tds_analiz_btn.clicked.connect(self._run_tds_ai_analiz)
        self.tds_analiz_btn.setEnabled(False)
        info_bar.addWidget(self.tds_analiz_btn)
        layout.addLayout(info_bar)

        # Genel durum gostergesi
        self.tds_durum_frame = QFrame()
        self.tds_durum_frame.setStyleSheet(
            f"QFrame {{ background: {self.theme['bg_card_solid']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 10px; }}")
        durum_lo = QHBoxLayout(self.tds_durum_frame)
        self.tds_durum_label = QLabel("Henuz analiz yapilmadi")
        self.tds_durum_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 14px; font-weight: bold;")
        durum_lo.addWidget(self.tds_durum_label)
        durum_lo.addStretch()
        self.tds_risk_label = QLabel("")
        self.tds_risk_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;")
        durum_lo.addWidget(self.tds_risk_label)
        layout.addWidget(self.tds_durum_frame)

        # Karsilastirma tablosu
        grp = QGroupBox("TDS Hedef vs Gercek Olcum")
        grp.setStyleSheet(f"""
            QGroupBox {{ border: 1px solid {self.theme['border']}; border-radius: 8px;
                margin-top: 10px; padding: 15px; background: {self.theme['bg_card_solid']}; }}
            QGroupBox::title {{ subcontrol-origin: margin; padding: 0 5px;
                color: {self.theme['primary']}; font-weight: bold; }}
        """)
        g_lo = QVBoxLayout(grp)
        self.tds_karsilastirma_table = QTableWidget()
        self.tds_karsilastirma_table.setColumnCount(7)
        self.tds_karsilastirma_table.setHorizontalHeaderLabels([
            "Parametre", "Birim", "TDS Hedef", "TDS Min", "TDS Max", "Gercek", "Durum"])
        self.tds_karsilastirma_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in [(1, 60), (2, 75), (3, 75), (4, 75), (5, 85), (6, 90)]:
            self.tds_karsilastirma_table.setColumnWidth(col, w)
        self.tds_karsilastirma_table.verticalHeader().setVisible(False)
        self.tds_karsilastirma_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tds_karsilastirma_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        g_lo.addWidget(self.tds_karsilastirma_table)
        layout.addWidget(grp, 1)

        # Takviye onerileri + Ozet
        alt_lo = QHBoxLayout()

        takviye_grp = QGroupBox("Takviye Onerileri")
        takviye_grp.setStyleSheet(grp.styleSheet())
        tk_lo = QVBoxLayout(takviye_grp)
        self.tds_takviye_text = QTextEdit()
        self.tds_takviye_text.setReadOnly(True)
        self.tds_takviye_text.setMaximumHeight(130)
        self.tds_takviye_text.setStyleSheet(
            f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; "
            f"border-radius: 6px; color: {self.theme['text']}; font-size: 12px;")
        tk_lo.addWidget(self.tds_takviye_text)
        alt_lo.addWidget(takviye_grp)

        trend_grp = QGroupBox("Trend ve Tahmin")
        trend_grp.setStyleSheet(grp.styleSheet())
        tr_lo = QVBoxLayout(trend_grp)
        self.tds_trend_text = QTextEdit()
        self.tds_trend_text.setReadOnly(True)
        self.tds_trend_text.setMaximumHeight(130)
        self.tds_trend_text.setStyleSheet(
            f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; "
            f"border-radius: 6px; color: {self.theme['text']}; font-size: 12px;")
        tr_lo.addWidget(self.tds_trend_text)
        alt_lo.addWidget(trend_grp)

        layout.addLayout(alt_lo)

        return widget

    def _on_banyo_changed(self):
        """Banyo secimi degistiginde limitleri ve TDS parametrelerini yukle"""
        self._load_banyo_limitleri()
        self._load_tds_parametreler()

    def _load_tds_parametreler(self):
        """Secili banyonun aktif TDS parametrelerini yukle"""
        banyo_id = self.banyo_combo.currentData()
        self.tds_parametreler = []
        self.tds_id = None

        if not banyo_id:
            self.tds_info_label.setText("Banyo seciniz - TDS bilgileri otomatik yuklenecek")
            self.tds_info_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px;")
            self.tds_analiz_btn.setEnabled(False)
            self.tds_karsilastirma_table.setRowCount(0)
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Aktif TDS bul
            cursor.execute("""
                SELECT TOP 1 t.id, t.tds_kodu, t.tds_adi, t.tedarikci
                FROM uretim.banyo_tds t
                WHERE t.banyo_id = ? AND t.aktif_mi = 1
                ORDER BY t.olusturma_tarihi DESC
            """, (banyo_id,))
            tds_row = cursor.fetchone()

            if not tds_row:
                self.tds_info_label.setText("Bu banyo icin TDS tanimi bulunamadi - Banyo limitleri kullanilacak")
                self.tds_info_label.setStyleSheet(f"color: {self.theme.get('warning', '#F59E0B')}; font-size: 13px;")
                # TDS yoksa banyo parametrelerinden yukle
                self._load_banyo_params_as_tds(banyo_id, cursor)
                return

            self.tds_id = tds_row[0]
            tds_bilgi = f"TDS: {tds_row[1]} - {tds_row[2]}"
            if tds_row[3]:
                tds_bilgi += f" [{tds_row[3]}]"
            self.tds_info_label.setText(tds_bilgi)
            self.tds_info_label.setStyleSheet(
                f"color: {self.theme.get('success', '#10B981')}; font-size: 13px; font-weight: bold;")

            # TDS parametrelerini yukle
            cursor.execute("""
                SELECT parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde, kritik_mi
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no
            """, (self.tds_id,))
            for r in cursor.fetchall():
                self.tds_parametreler.append({
                    "parametre_kodu": r[0], "parametre_adi": r[1], "birim": r[2],
                    "tds_min": float(r[3]) if r[3] else None,
                    "tds_hedef": float(r[4]) if r[4] else None,
                    "tds_max": float(r[5]) if r[5] else None,
                    "tolerans_yuzde": float(r[6]) if r[6] else 10.0,
                    "kritik_mi": bool(r[7]),
                })

            self.tds_analiz_btn.setEnabled(bool(self.tds_parametreler))

        except Exception as e:
            self.tds_info_label.setText(f"TDS yuklenemedi: {e}")
            print(f"TDS yukleme hatasi: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_banyo_params_as_tds(self, banyo_id, cursor):
        """TDS yoksa banyo tanimindaki parametreleri TDS olarak kullan"""
        try:
            cursor.execute("""
                SELECT sicaklik_min, sicaklik_hedef, sicaklik_max,
                       ph_min, ph_hedef, ph_max,
                       iletkenlik_min, iletkenlik_hedef, iletkenlik_max,
                       kati_madde_min, kati_madde_hedef, kati_madde_max,
                       pb_orani_min, pb_orani_hedef, pb_orani_max,
                       solvent_min, solvent_hedef, solvent_max,
                       meq_min, meq_hedef, meq_max
                FROM uretim.banyo_tanimlari WHERE id = ?
            """, (banyo_id,))
            row = cursor.fetchone()
            if not row:
                return

            param_listesi = [
                ("sicaklik", "Sicaklik", "°C", 0, 1, 2),
                ("ph", "pH", "", 3, 4, 5),
                ("iletkenlik", "Iletkenlik", "uS/cm", 6, 7, 8),
                ("kati_madde", "Kati Madde", "%", 9, 10, 11),
                ("pb_orani", "P/B Orani", "", 12, 13, 14),
                ("solvent", "Solvent", "%", 15, 16, 17),
                ("meq", "MEQ", "meq", 18, 19, 20),
            ]

            self.tds_parametreler = []
            for kod, adi, birim, mi, hi, mx in param_listesi:
                if row[hi] is not None and row[hi] != 0:
                    self.tds_parametreler.append({
                        "parametre_kodu": kod, "parametre_adi": adi, "birim": birim,
                        "tds_min": float(row[mi]) if row[mi] else None,
                        "tds_hedef": float(row[hi]) if row[hi] else None,
                        "tds_max": float(row[mx]) if row[mx] else None,
                        "tolerans_yuzde": 10.0, "kritik_mi": False,
                    })

            self.tds_analiz_btn.setEnabled(bool(self.tds_parametreler))

        except Exception as e:
            print(f"Banyo param TDS yuklenemedi: {e}")

    def _get_current_olcumler(self):
        """Formdaki mevcut analiz degerlerini dict olarak don"""
        return {
            "sicaklik": self.sicaklik_input.value() or None,
            "ph": self.ph_input.value() or None,
            "iletkenlik": self.iletkenlik_input.value() or None,
            "kati_madde": self.kati_madde_input.value() or None,
            "pb_orani": self.pb_orani_input.value() or None,
            "solvent": self.solvent_input.value() or None,
            "meq": self.meq_input.value() or None,
            "toplam_asit": self.toplam_asit_input.value() or None,
            "serbest_asit": self.serbest_asit_input.value() or None,
        }

    def _run_tds_ai_analiz(self):
        """TDS AI analizini calistir"""
        if not self.tds_parametreler:
            QMessageBox.warning(self, "Uyari", "TDS parametreleri bulunamadi!")
            return

        banyo_id = self.banyo_combo.currentData()
        if not banyo_id:
            QMessageBox.warning(self, "Uyari", "Lutfen banyo seciniz!")
            return

        try:
            from core.ai_analiz_service import AIAnalizService
            service = AIAnalizService()

            # Formdaki mevcut degerleri al
            son_olcumler = self._get_current_olcumler()

            # Son 30 gunluk veri serisini DB'den al (trend icin)
            veri_serisi = []
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tarih, sicaklik, ph, iletkenlik, kati_madde_yuzde,
                           pb_orani, solvent_yuzde, meq_degeri,
                           toplam_asitlik, serbest_asitlik
                    FROM uretim.banyo_analiz_sonuclari
                    WHERE banyo_id = ? AND tarih >= DATEADD(day, -30, GETDATE())
                    ORDER BY tarih
                """, (banyo_id,))
                col_map = {
                    1: "sicaklik", 2: "ph", 3: "iletkenlik", 4: "kati_madde",
                    5: "pb_orani", 6: "solvent", 7: "meq",
                    8: "toplam_asit", 9: "serbest_asit",
                }
                for row in cursor.fetchall():
                    tarih = row[0]
                    for idx, param_kod in col_map.items():
                        if row[idx] is not None:
                            veri_serisi.append({
                                "parametre": param_kod,
                                "tarih": tarih,
                                "deger": float(row[idx]),
                            })
            except Exception as e:
                print(f"Veri serisi yuklenemedi: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass

            # Tam analiz calistir
            sonuc = service.tam_analiz(
                banyo_id=banyo_id,
                tds_parametreler=self.tds_parametreler,
                son_olcumler=son_olcumler,
                veri_serisi=veri_serisi,
            )

            # Karsilastirma tablosunu doldur
            karsilastirma = sonuc.get("karsilastirma", [])
            self.tds_karsilastirma_table.setRowCount(len(karsilastirma))
            for i, k in enumerate(karsilastirma):
                self.tds_karsilastirma_table.setItem(i, 0, QTableWidgetItem(k.get("parametre", "")))
                self.tds_karsilastirma_table.setItem(i, 1, QTableWidgetItem(k.get("birim", "")))
                self.tds_karsilastirma_table.setItem(i, 2, QTableWidgetItem(
                    f"{k['tds_hedef']:.2f}" if k.get("tds_hedef") else "-"))
                self.tds_karsilastirma_table.setItem(i, 3, QTableWidgetItem(
                    f"{k['tds_min']:.2f}" if k.get("tds_min") else "-"))
                self.tds_karsilastirma_table.setItem(i, 4, QTableWidgetItem(
                    f"{k['tds_max']:.2f}" if k.get("tds_max") else "-"))
                self.tds_karsilastirma_table.setItem(i, 5, QTableWidgetItem(
                    f"{k['gercek']:.2f}" if k.get("gercek") is not None else "-"))

                durum = k.get("durum", "")
                sapma = k.get("sapma_yuzde", 0)
                durum_txt = f"{durum} ({sapma:.0f}%)"
                durum_item = QTableWidgetItem(durum_txt)
                durum_renk = {"NORMAL": "#22C55E", "UYARI": "#F59E0B", "KRITIK": "#EF4444"}
                durum_item.setForeground(QColor(durum_renk.get(durum, "#ffffff")))
                self.tds_karsilastirma_table.setItem(i, 6, durum_item)

            # Risk seviyesi guncelle
            risk = sonuc.get("risk_seviyesi", "NORMAL")
            risk_map = {"NORMAL": ("NORMAL", "#22C55E"), "UYARI": ("UYARI", "#F59E0B"), "KRITIK": ("KRITIK", "#EF4444")}
            risk_txt, risk_renk = risk_map.get(risk, ("?", "#fff"))
            self.tds_durum_label.setText(f"Risk Seviyesi: {risk_txt}")
            self.tds_durum_label.setStyleSheet(f"color: {risk_renk}; font-size: 14px; font-weight: bold;")
            self.tds_durum_frame.setStyleSheet(
                f"QFrame {{ background: {self.theme['bg_card_solid']}; "
                f"border: 2px solid {risk_renk}; border-radius: 8px; padding: 10px; }}")

            uyari_say = sum(1 for k in karsilastirma if k.get("durum") != "NORMAL")
            self.tds_risk_label.setText(f"{uyari_say} parametre limitler disinda" if uyari_say else "Tum parametreler normal")

            # Takviye onerileri
            takviye = sonuc.get("takviye", [])
            if takviye:
                takviye_satirlari = []
                for t in takviye:
                    takviye_satirlari.append(
                        f"[{t['oncelik']}] {t['parametre']}: {t['kimyasal']} - "
                        f"{t['miktar']:.2f} {t['birim']}")
                    if t.get("aciklama"):
                        takviye_satirlari.append(f"  {t['aciklama']}")
                self.tds_takviye_text.setPlainText("\n".join(takviye_satirlari))
            else:
                self.tds_takviye_text.setPlainText("Takviye onerisi yok - parametreler normal.")

            # Trend ve tahmin
            trend = sonuc.get("trend", [])
            tahmin = sonuc.get("tahmin", [])
            trend_satirlari = []
            if trend:
                trend_satirlari.append("TREND (Son 30 gun):")
                for t in trend:
                    yorum_map = {"artan": "Artan", "azalan": "Azalan", "stabil": "Stabil"}
                    trend_satirlari.append(
                        f"  {t['parametre']}: {yorum_map.get(t['yorum'], t['yorum'])} "
                        f"(Son: {t['son_deger']:.2f}, Ort: {t['ortalama']:.2f}, "
                        f"Veri: {t['veri_sayisi']} olcum)")
            if tahmin:
                trend_satirlari.append("\nTAHMIN (7 gun sonra):")
                for t in tahmin:
                    trend_satirlari.append(
                        f"  {t['parametre']}: {t['tahmini_7gun']:.2f} "
                        f"(Mevcut: {t['mevcut']:.2f}, Risk: {t['risk']})")
            self.tds_trend_text.setPlainText("\n".join(trend_satirlari) if trend_satirlari else "Yeterli veri yok (en az 2 olcum gerekli).")

            # Sonuclari DB'ye kaydet
            if self.tds_id:
                try:
                    service.sonuclari_kaydet(banyo_id, self.tds_id, "TAM_ANALIZ", sonuc)
                except Exception as e:
                    print(f"AI analiz kayit hatasi: {e}")

        except Exception as e:
            QMessageBox.critical(self, "AI Analiz Hatasi", str(e))
            import traceback
            traceback.print_exc()

    def _create_notlar_tab(self):
        """Notlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.notlar_input = QTextEdit()
        self.notlar_input.setPlaceholderText("Analiz ile ilgili notlarınızı buraya yazabilirsiniz...")
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        self.notlar_input.setStyleSheet(f"""
            QTextEdit {{
                background: {self.theme['bg_input']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 10px;
                color: {self.theme['text']};
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.notlar_input)
        
        return widget
    
    def _create_param_spinbox(self, min_val, max_val, suffix, value, decimals=0):
        """Parametre spinbox oluşturur"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setDecimals(decimals)
        if suffix:
            spinbox.setSuffix(suffix)
        spinbox.setValue(value or 0)
        spinbox.setMinimumWidth(150)
        return spinbox
    
    def _load_banyolar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT b.id, b.kod, b.ad, h.kod
                FROM uretim.banyo_tanimlari b
                JOIN tanim.uretim_hatlari h ON b.hat_id=h.id
                WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod""")
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[3]} / {row[1]} - {row[2]}", row[0])
            if self.data.get('banyo_id'):
                idx = self.banyo_combo.findData(self.data['banyo_id'])
                if idx >= 0:
                    self.banyo_combo.setCurrentIndex(idx)
                    self._on_banyo_changed()
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_analistler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, soyad FROM ik.personeller WHERE aktif_mi=1 ORDER BY ad")
            for row in cursor.fetchall():
                self.analist_combo.addItem(f"{row[1]} {row[2]}", row[0])
            if self.data.get('analist_id'):
                idx = self.analist_combo.findData(self.data['analist_id'])
                if idx >= 0: self.analist_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_banyo_limitleri(self):
        """Seçili banyonun limit değerlerini yükler"""
        banyo_id = self.banyo_combo.currentData()
        if not banyo_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sicaklik_min, sicaklik_max, sicaklik_hedef,
                       ph_min, ph_max, ph_hedef,
                       iletkenlik_min, iletkenlik_max, iletkenlik_hedef,
                       kati_madde_min, kati_madde_max, kati_madde_hedef,
                       pb_orani_min, pb_orani_max, pb_orani_hedef,
                       solvent_min, solvent_max, solvent_hedef,
                       meq_min, meq_max, meq_hedef
                FROM uretim.banyo_tanimlari WHERE id = ?
            """, (banyo_id,))
            row = cursor.fetchone()
            if row:
                self.banyo_limitleri = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            print(f"Limit yukleme hatasi: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _validate_limits(self):
        """Parametre limitlerini kontrol eder ve uyarı verir"""
        if not self.banyo_limitleri:
            return True
        
        uyarilar = []
        
        # Sıcaklık kontrolü
        sic = self.sicaklik_input.value()
        if self.banyo_limitleri.get('sicaklik_min') and sic < self.banyo_limitleri['sicaklik_min']:
            uyarilar.append(f"⚠️ Sıcaklık limit altında! (Min: {self.banyo_limitleri['sicaklik_min']}°C)")
        if self.banyo_limitleri.get('sicaklik_max') and sic > self.banyo_limitleri['sicaklik_max']:
            uyarilar.append(f"⚠️ Sıcaklık limit üstünde! (Max: {self.banyo_limitleri['sicaklik_max']}°C)")
        
        # pH kontrolü
        ph = self.ph_input.value()
        if self.banyo_limitleri.get('ph_min') and ph < self.banyo_limitleri['ph_min']:
            uyarilar.append(f"⚠️ pH limit altında! (Min: {self.banyo_limitleri['ph_min']})")
        if self.banyo_limitleri.get('ph_max') and ph > self.banyo_limitleri['ph_max']:
            uyarilar.append(f"⚠️ pH limit üstünde! (Max: {self.banyo_limitleri['ph_max']})")
        
        # İletkenlik kontrolü
        ilet = self.iletkenlik_input.value()
        if self.banyo_limitleri.get('iletkenlik_min') and ilet < self.banyo_limitleri['iletkenlik_min']:
            uyarilar.append(f"⚠️ İletkenlik limit altında! (Min: {self.banyo_limitleri['iletkenlik_min']} µS/cm)")
        if self.banyo_limitleri.get('iletkenlik_max') and ilet > self.banyo_limitleri['iletkenlik_max']:
            uyarilar.append(f"⚠️ İletkenlik limit üstünde! (Max: {self.banyo_limitleri['iletkenlik_max']} µS/cm)")
        
        # Katı madde kontrolü
        kati = self.kati_madde_input.value()
        if self.banyo_limitleri.get('kati_madde_min') and kati < self.banyo_limitleri['kati_madde_min']:
            uyarilar.append(f"⚠️ Katı madde limit altında! (Min: {self.banyo_limitleri['kati_madde_min']}%)")
        if self.banyo_limitleri.get('kati_madde_max') and kati > self.banyo_limitleri['kati_madde_max']:
            uyarilar.append(f"⚠️ Katı madde limit üstünde! (Max: {self.banyo_limitleri['kati_madde_max']}%)")
        
        if uyarilar:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Parametre Limitleri Dışında!")
            msg.setText("Bazı parametreler limit değerlerin dışında:\n\n" + "\n".join(uyarilar))
            msg.setInformativeText("\nYine de kaydetmek istiyor musunuz?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            return msg.exec() == QMessageBox.Yes
        
        return True
    
    def _save(self):
        banyo_id = self.banyo_combo.currentData()
        analist_id = self.analist_combo.currentData()
        
        if not banyo_id or not analist_id:
            QMessageBox.warning(self, "Uyarı", "Banyo ve Analist seçimi zorunludur!")
            return
        
        # Limit kontrolü
        if not self._validate_limits():
            return
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                banyo_id,
                self.tarih_input.dateTime().toPython(),
                analist_id,
                self.sicaklik_input.value() or None,
                self.ph_input.value() or None,
                self.iletkenlik_input.value() or None,
                self.toplam_asit_input.value() or None,
                self.serbest_asit_input.value() or None,
                self.notlar_input.toPlainText().strip() or None
            )

            if self.analiz_id:
                cursor.execute("""UPDATE uretim.banyo_analiz_sonuclari SET
                    banyo_id=?, tarih=?, analist_id=?, sicaklik=?, ph=?, iletkenlik=?,
                    toplam_asitlik=?, serbest_asitlik=?, notlar=?
                    WHERE id=?""", params + (self.analiz_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_analiz_sonuclari
                    (banyo_id, tarih, analist_id, sicaklik, ph, iletkenlik,
                     toplam_asitlik, serbest_asitlik, notlar)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", params)

                # Analiz ID'yi al (yeni eklenen kayıt)
                cursor.execute("SELECT @@IDENTITY")
                analiz_id = cursor.fetchone()[0]

            conn.commit()
            LogManager.log_insert('lab', 'uretim.banyo_analiz_sonuclari', None, 'Analiz sonucu kaydedildi')

            # LAB EVENT KAYDI
            try:
                # Durum kontrolu
                durum = self._check_analiz_durum(banyo_id, params)

                if durum in ['UYARI', 'KRITIK']:
                    # Lab event tablosuna yaz
                    cursor.execute("""
                        INSERT INTO uretim.lab_event_log
                        (banyo_id, analiz_id, event_tipi, sicaklik, ph,
                         iletkenlik, toplam_asitlik, serbest_asitlik, notlar, analist_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        banyo_id,
                        analiz_id if not self.analiz_id else self.analiz_id,
                        f'LAB_ANALIZ_{durum}',
                        params[3], params[4], params[5],
                        params[6], params[7], params[8],
                        analist_id
                    ))
                    conn.commit()
                    print(f"Lab event kaydedildi: BANYO-{banyo_id} -> {durum}")

                    # NEXOR BILDIRIM SISTEMI (WhatsApp + Email otomatik)
                    try:
                        from core.bildirim_tetikleyici import BildirimTetikleyici
                        # Banyo adını al
                        cursor.execute("SELECT kod + ' - ' + ad FROM uretim.banyo_tanimlari WHERE id = ?", (banyo_id,))
                        b_row = cursor.fetchone()
                        b_adi = b_row[0] if b_row else f"Banyo-{banyo_id}"

                        # Detay bilgisi oluştur
                        detay_parts = []
                        if params[3]:
                            detay_parts.append(f"Sicaklik: {params[3]:.1f}°C")
                        if params[4]:
                            detay_parts.append(f"pH: {params[4]:.2f}")
                        if params[5]:
                            detay_parts.append(f"Iletkenlik: {params[5]:.0f}")

                        BildirimTetikleyici.lab_analiz_hatali(
                            analiz_id=analiz_id if not self.analiz_id else self.analiz_id,
                            banyo_adi=b_adi,
                            durum=durum,
                            detay=', '.join(detay_parts),
                        )
                    except Exception as bt_err:
                        print(f"Bildirim tetikleyici hatasi: {bt_err}")

            except Exception as e:
                print(f"Lab event hatasi (onemsiz): {e}")

            QMessageBox.information(self, "Basarili", "Analiz sonucu kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit sirasinda hata:\n{str(e)}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _check_analiz_durum(self, banyo_id, params):
        """Analiz sonucuna göre durum belirle: NORMAL / UYARI / KRITIK"""
        try:
            # Banyo limitlerini al
            if not self.banyo_limitleri or self.banyo_limitleri.get('banyo_id') != banyo_id:
                conn2 = None
                try:
                    conn2 = get_db_connection()
                    cursor = conn2.cursor()
                    cursor.execute("""
                        SELECT sicaklik_min, sicaklik_max, sicaklik_hedef,
                               ph_min, ph_max, ph_hedef,
                               toplam_asit_min, toplam_asit_max
                        FROM uretim.banyo_tanimlari WHERE id = ?
                    """, (banyo_id,))
                    row = cursor.fetchone()
                finally:
                    if conn2:
                        try: conn2.close()
                        except Exception: pass

                if row:
                    self.banyo_limitleri = {
                        'banyo_id': banyo_id,
                        'sicaklik_min': row[0], 'sicaklik_max': row[1], 'sicaklik_hedef': row[2],
                        'ph_min': row[3], 'ph_max': row[4], 'ph_hedef': row[5],
                        'asit_min': row[6], 'asit_max': row[7]
                    }
            
            # Parametrelerden değerleri al
            sicaklik = float(params[3]) if params[3] else None
            ph = float(params[4]) if params[4] else None
            asit = float(params[6]) if params[6] else None
            
            durum = 'NORMAL'
            
            # Sıcaklık kontrolü
            if sicaklik and self.banyo_limitleri.get('sicaklik_min') and self.banyo_limitleri.get('sicaklik_max'):
                s_min = float(self.banyo_limitleri['sicaklik_min'])
                s_max = float(self.banyo_limitleri['sicaklik_max'])
                
                if sicaklik < s_min or sicaklik > s_max:
                    hedef = float(self.banyo_limitleri.get('sicaklik_hedef') or (s_min + s_max) / 2)
                    if abs(sicaklik - hedef) > 10:
                        durum = 'KRITIK'
                    else:
                        durum = 'UYARI'
            
            # pH kontrolü
            if ph and self.banyo_limitleri.get('ph_min') and self.banyo_limitleri.get('ph_max'):
                ph_min = float(self.banyo_limitleri['ph_min'])
                ph_max = float(self.banyo_limitleri['ph_max'])
                
                if ph < ph_min or ph > ph_max:
                    hedef = float(self.banyo_limitleri.get('ph_hedef') or (ph_min + ph_max) / 2)
                    if abs(ph - hedef) > 1:
                        durum = 'KRITIK'
                    elif durum != 'KRITIK':
                        durum = 'UYARI'
            
            # Asitlik kontrolü
            if asit and self.banyo_limitleri.get('asit_min') and self.banyo_limitleri.get('asit_max'):
                a_min = float(self.banyo_limitleri['asit_min'])
                a_max = float(self.banyo_limitleri['asit_max'])
                
                if asit < a_min or asit > a_max:
                    if durum != 'KRITIK':
                        durum = 'UYARI'
            
            return durum
            
        except Exception as e:
            print(f"Durum kontrol hatası: {e}")
            return 'NORMAL'


class LabAnalizPage(BasePage):
    """Banyo Analiz Sonuçları Listesi"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        header = QHBoxLayout()
        title = QLabel("🔬 Banyo Analiz Sonuçları")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"color: {self.theme['text_muted']};")
        header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout()
        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("Tüm Banyolar", None)
        self._load_banyo_filter()
        self.banyo_combo.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']}; min-width: 200px;")
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.banyo_combo)
        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Banyo Analiz Sonuclari"))

        add_btn = QPushButton("➕ Yeni Analiz")
        add_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px; gridline-color: {self.theme['border']}; color: {self.theme['text']}; }}
            QTableWidget::item {{ padding: 6px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}; }}
            QHeaderView::section {{ background: {self.theme['bg_main']}; color: {self.theme['text']}; padding: 8px; border: none; border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """)
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "Banyo", "Tarih", "Sıcaklık", "pH", "İletkenlik", 
            "Katı Madde", "P/B", "Solvent", "MEQ", "Demir", "Çinko", "İşlem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 60)
        self.table.setColumnWidth(8, 70)
        self.table.setColumnWidth(9, 60)
        self.table.setColumnWidth(10, 60)
        self.table.setColumnWidth(11, 60)
        self.table.setColumnWidth(12, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table, 1)
    
    def _load_banyo_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT b.id, b.kod, h.kod FROM uretim.banyo_tanimlari b
                JOIN tanim.uretim_hatlari h ON b.hat_id=h.id WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod""")
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[2]} / {row[1]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """SELECT a.id, b.kod + ' - ' + b.ad, a.tarih, a.sicaklik, a.ph, a.iletkenlik,
                     a.kati_madde_yuzde, a.pb_orani, a.solvent_yuzde, a.meq_degeri,
                     a.demir_ppm, a.cinko_ppm,
                     b.sicaklik_min, b.sicaklik_max, b.ph_min, b.ph_max,
                     b.kati_madde_min, b.kati_madde_max
                     FROM uretim.banyo_analiz_sonuclari a
                     JOIN uretim.banyo_tanimlari b ON a.banyo_id=b.id
                     WHERE 1=1"""
            params = []

            banyo_id = self.banyo_combo.currentData()
            if banyo_id:
                sql += " AND a.banyo_id=?"
                params.append(banyo_id)

            sql += " ORDER BY a.tarih DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                
                tarih = row[2].strftime("%d.%m.%Y %H:%M") if row[2] else '-'
                self.table.setItem(i, 2, QTableWidgetItem(tarih))
                
                # Sıcaklık (limit kontrolü)
                sic_item = QTableWidgetItem(f"{row[3]:.1f}°C" if row[3] else '-')
                if row[3] and row[12] and row[13]:
                    if row[3] < row[12] or row[3] > row[13]:
                        sic_item.setForeground(QColor("#ff4444"))
                    else:
                        sic_item.setForeground(QColor("#44ff44"))
                self.table.setItem(i, 3, sic_item)
                
                # pH (limit kontrolü)
                ph_item = QTableWidgetItem(f"{row[4]:.2f}" if row[4] else '-')
                if row[4] and row[14] and row[15]:
                    if row[4] < row[14] or row[4] > row[15]:
                        ph_item.setForeground(QColor("#ff4444"))
                    else:
                        ph_item.setForeground(QColor("#44ff44"))
                self.table.setItem(i, 4, ph_item)
                
                self.table.setItem(i, 5, QTableWidgetItem(f"{row[5]:.0f}" if row[5] else '-'))
                
                # Katı Madde (YENİ! - limit kontrolü)
                km_item = QTableWidgetItem(f"{row[6]:.2f}%" if row[6] else '-')
                if row[6] and row[16] and row[17]:
                    if row[6] < row[16] or row[6] > row[17]:
                        km_item.setForeground(QColor("#ff4444"))
                    else:
                        km_item.setForeground(QColor("#44ff44"))
                self.table.setItem(i, 6, km_item)
                
                # P/B Oranı (YENİ!)
                self.table.setItem(i, 7, QTableWidgetItem(f"{row[7]:.2f}" if row[7] else '-'))
                
                # Solvent (YENİ!)
                self.table.setItem(i, 8, QTableWidgetItem(f"{row[8]:.2f}%" if row[8] else '-'))
                
                # MEQ (YENİ!)
                self.table.setItem(i, 9, QTableWidgetItem(f"{row[9]:.0f}" if row[9] else '-'))
                
                self.table.setItem(i, 10, QTableWidgetItem(f"{row[10]:.0f}" if row[10] else '-'))
                self.table.setItem(i, 11, QTableWidgetItem(f"{row[11]:.0f}" if row[11] else '-'))
                
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 12, widget)
                self.table.setRowHeight(i, 42)
            
            self.stat_label.setText(f"Toplam: {len(rows)} analiz")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _add_new(self):
        dlg = AnalizDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, aid):
        dlg = AnalizDialog(self.theme, aid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _delete_item(self, aid):
        if QMessageBox.question(self, "Onay", "Bu analiz kaydini silmek istediginize emin misiniz?") == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.banyo_analiz_sonuclari WHERE id=?", (aid,))
                conn.commit()
                LogManager.log_delete('lab', 'uretim.banyo_analiz_sonuclari', None, 'Kayit silindi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass

