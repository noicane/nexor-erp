# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - 8D / CAPA Sayfası
8D Problem Çözme Metodolojisi ve Düzeltici/Önleyici Faaliyetler
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QGridLayout, QGroupBox, QFormLayout,
    QDateEdit, QTabWidget, QWidget, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


# 8D Adımları
D_ADIMLARI = {
    0: ("D0", "Hazırlık", "Problemi tanımlayın ve 8D'ye ihtiyaç olup olmadığını belirleyin"),
    1: ("D1", "Ekip Oluşturma", "Problem çözme ekibini oluşturun"),
    2: ("D2", "Problem Tanımı", "Problemi detaylı olarak tanımlayın (5W2H)"),
    3: ("D3", "Geçici Önlemler", "Müşteriyi korumak için acil önlemler alın"),
    4: ("D4", "Kök Neden Analizi", "Kök nedenleri belirleyin (5 Neden, Balık Kılçığı)"),
    5: ("D5", "Kalıcı Düzeltici Faaliyetler", "Kök nedenleri ortadan kaldıracak kalıcı çözümler planlayın"),
    6: ("D6", "Uygulama ve Doğrulama", "Düzeltici faaliyetleri uygulayın ve etkinliğini doğrulayın"),
    7: ("D7", "Önleyici Faaliyetler", "Tekrarı önlemek için sistem değişiklikleri yapın"),
    8: ("D8", "Ekip Takdiri", "Ekibi takdir edin ve öğrenilen dersleri paylaşın")
}


class Yeni8DDialog(QDialog):
    """Yeni 8D Raporu oluşturma dialog'u"""
    
    def __init__(self, theme: dict, uygunsuzluk_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.uygunsuzluk_id = uygunsuzluk_id
        self.setWindowTitle("Yeni 8D Raporu")
        self.setMinimumSize(750, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {self.theme.get('text', '#ffffff')}; }}
            QGroupBox {{ 
                color: {self.theme.get('primary', '#3b82f6')}; 
                font-weight: bold; 
                border: 1px solid {self.theme.get('border')}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        title = QLabel("📋 Yeni 8D Raporu Oluştur")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Kaynak seçimi
        kaynak_group = QGroupBox("Kaynak Bilgileri")
        kaynak_form = QFormLayout()
        
        self.cmb_uygunsuzluk = QComboBox()
        self.cmb_uygunsuzluk.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_uygunsuzluklar()
        if self.uygunsuzluk_id:
            for i in range(self.cmb_uygunsuzluk.count()):
                if self.cmb_uygunsuzluk.itemData(i) == self.uygunsuzluk_id:
                    self.cmb_uygunsuzluk.setCurrentIndex(i)
                    break
        kaynak_form.addRow("Uygunsuzluk Kaydı:", self.cmb_uygunsuzluk)
        
        kaynak_group.setLayout(kaynak_form)
        layout.addWidget(kaynak_group)
        
        # D0 - Problem Tanımı
        d0_group = QGroupBox("D0 - Problem Tanımı")
        d0_layout = QVBoxLayout()
        
        d0_layout.addWidget(QLabel("Problem Özeti:"))
        self.txt_problem = QTextEdit()
        self.txt_problem.setMaximumHeight(80)
        self.txt_problem.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self.txt_problem.setPlaceholderText("Problemi kısaca açıklayın...")
        d0_layout.addWidget(self.txt_problem)
        
        d0_group.setLayout(d0_layout)
        layout.addWidget(d0_group)
        
        # D1 - Ekip
        d1_group = QGroupBox("D1 - Ekip Lideri")
        d1_form = QFormLayout()
        
        self.cmb_lider = QComboBox()
        self.cmb_lider.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_personel()
        d1_form.addRow("Ekip Lideri:", self.cmb_lider)
        
        d1_group.setLayout(d1_form)
        layout.addWidget(d1_group)
        
        # Hedef tarih
        tarih_layout = QHBoxLayout()
        tarih_layout.addWidget(QLabel("Hedef Kapanış Tarihi:"))
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(14))
        self.date_hedef.setCalendarPopup(True)
        self.date_hedef.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        tarih_layout.addWidget(self.date_hedef)
        tarih_layout.addStretch()
        layout.addLayout(tarih_layout)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 24px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("🚀 8D Başlat")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_uygunsuzluklar(self):
        """Açık uygunsuzluk kayıtlarını yükle"""
        self.cmb_uygunsuzluk.clear()
        self.cmb_uygunsuzluk.addItem("-- Yeni (Uygunsuzluk Olmadan) --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kayit_no + ' - ' + LEFT(hata_tanimi, 50) 
                FROM kalite.uygunsuzluklar 
                WHERE durum IN ('AÇIK', 'İŞLEMDE')
                ORDER BY kayit_tarihi DESC
            """)
            for row in cursor.fetchall():
                self.cmb_uygunsuzluk.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Uygunsuzluk yükleme hatası: {e}")
    
    def _load_personel(self):
        """Personel listesi"""
        self.cmb_lider.clear()
        self.cmb_lider.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_lider.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Personel yükleme hatası: {e}")
    
    def _kaydet(self):
        """8D Raporu başlat - Düzeltilmiş versiyon"""
        lider_id = self.cmb_lider.currentData()
        if not lider_id:
            QMessageBox.warning(self, "Uyarı", "Ekip lideri seçilmelidir!")
            return
        
        problem = self.txt_problem.toPlainText().strip()
        if not problem:
            QMessageBox.warning(self, "Uyarı", "Problem tanımı girilmelidir!")
            return
        
        uygunsuzluk_id = self.cmb_uygunsuzluk.currentData()
        hedef_tarih = self.date_hedef.date().toPython()
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Uygunsuzluk seçilmediyse otomatik oluştur
            if not uygunsuzluk_id:
                # Yeni kayıt numarası üret
                cursor.execute("""
                    SELECT 'UYG-8D-' + FORMAT(GETDATE(), 'yyMM') + '-' + 
                           RIGHT('000' + CAST(ISNULL(
                               (SELECT COUNT(*) + 1 FROM kalite.uygunsuzluklar 
                                WHERE kayit_no LIKE 'UYG-8D-' + FORMAT(GETDATE(), 'yyMM') + '%'), 1
                           ) AS VARCHAR), 3)
                """)
                kayit_no = cursor.fetchone()[0]
                
                # Yeni uygunsuzluk kaydı oluştur
                cursor.execute("""
                    INSERT INTO kalite.uygunsuzluklar (
                        uuid, kayit_no, kayit_tipi, kayit_tarihi, bildiren_id,
                        hata_tanimi, tespit_yeri, oncelik, durum, sorumlu_id,
                        hedef_kapanis_tarihi, olusturma_tarihi, guncelleme_tarihi
                    ) 
                    OUTPUT INSERTED.id
                    VALUES (
                        NEWID(), ?, '8D', CAST(GETDATE() AS DATE), ?,
                        ?, 'DAHİLİ', 'ORTA', 'İŞLEMDE', ?,
                        ?, GETDATE(), GETDATE()
                    )
                """, (kayit_no, lider_id, problem, lider_id, hedef_tarih))
                
                uygunsuzluk_id = cursor.fetchone()[0]
            
            # D0 - Hazırlık (Tamamlandı olarak işaretle)
            cursor.execute("""
                INSERT INTO kalite.uygunsuzluk_aksiyonlar (
                    uuid, uygunsuzluk_id, aksiyon_tipi, d_adimi, aciklama,
                    sorumlu_id, hedef_tarih, durum, olusturma_tarihi
                ) VALUES (
                    NEWID(), ?, '8D', 0, ?,
                    ?, ?, 'TAMAMLANDI', GETDATE()
                )
            """, (uygunsuzluk_id, f"8D Raporu Başlatıldı - {problem}", lider_id, hedef_tarih))
            
            # D1 - Ekip oluşturma (Açık olarak)
            cursor.execute("""
                INSERT INTO kalite.uygunsuzluk_aksiyonlar (
                    uuid, uygunsuzluk_id, aksiyon_tipi, d_adimi, aciklama,
                    sorumlu_id, hedef_tarih, durum, olusturma_tarihi
                ) VALUES (
                    NEWID(), ?, '8D', 1, ?,
                    ?, ?, 'AÇIK', GETDATE()
                )
            """, (uygunsuzluk_id, "Ekip oluşturulacak", lider_id, hedef_tarih))
            
            # Uygunsuzluk durumunu güncelle
            cursor.execute("""
                UPDATE kalite.uygunsuzluklar 
                SET durum = 'İŞLEMDE', 
                    hedef_kapanis_tarihi = ?,
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (hedef_tarih, uygunsuzluk_id))
            
            conn.commit()
            LogManager.log_update('kalite', 'kalite.uygunsuzluklar', None, 'Durum guncellendi')

            # Bildirim: 8D Raporu / Uygunsuzluk açıldı
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                BildirimTetikleyici.uygunsuzluk_acildi(
                    kayit_id=uygunsuzluk_id,
                    kayit_no=kayit_no,
                    urun_adi=f"8D: {problem[:50]}",
                )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            QMessageBox.information(self, "Başarılı", "8D Raporu başlatıldı!")
            self.accept()
            
        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız: {e}")
        
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class Detay8DDialog(QDialog):
    """8D Detay ve adım yönetimi dialog'u"""
    
    def __init__(self, theme: dict, uygunsuzluk_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.uygunsuzluk_id = uygunsuzluk_id
        self.setWindowTitle("8D Raporu Detayı")
        self.setMinimumSize(1000, 750)
        self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        """Verileri yükle"""
        self.kayit = {}
        self.aksiyonlar = {}
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.kayit_no, u.kayit_tipi, u.kayit_tarihi, u.hata_tanimi,
                       c.unvan, s.urun_adi, u.lot_no, u.durum,
                       p.ad + ' ' + p.soyad as sorumlu, u.hedef_kapanis_tarihi
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                LEFT JOIN ik.personeller p ON u.sorumlu_id = p.id
                WHERE u.id = ?
            """, (self.uygunsuzluk_id,))
            
            row = cursor.fetchone()
            if row:
                self.kayit = {
                    'id': row[0], 'kayit_no': row[1], 'tip': row[2], 'tarih': row[3],
                    'hata_tanimi': row[4], 'cari': row[5], 'urun': row[6], 'lot': row[7],
                    'durum': row[8], 'sorumlu': row[9], 'hedef': row[10]
                }
            
            cursor.execute("""
                SELECT a.id, a.d_adimi, a.aciklama, a.durum, a.hedef_tarih,
                       a.tamamlanma_tarihi, p.ad + ' ' + p.soyad as sorumlu
                FROM kalite.uygunsuzluk_aksiyonlar a
                LEFT JOIN ik.personeller p ON a.sorumlu_id = p.id
                WHERE a.uygunsuzluk_id = ? AND a.aksiyon_tipi = '8D'
                ORDER BY a.d_adimi, a.olusturma_tarihi
            """, (self.uygunsuzluk_id,))
            
            for row in cursor.fetchall():
                d = row[1] or 0
                if d not in self.aksiyonlar:
                    self.aksiyonlar[d] = []
                self.aksiyonlar[d].append({
                    'id': row[0], 'aciklama': row[2], 'durum': row[3],
                    'hedef': row[4], 'tamamlanma': row[5], 'sorumlu': row[6]
                })
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {self.theme.get('text', '#ffffff')}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"📋 8D Raporu - {self.kayit.get('kayit_no', '')}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        header.addWidget(title)
        
        durum = self.kayit.get('durum', '')
        durum_colors = {'AÇIK': self.theme.get('warning'), 'İŞLEMDE': self.theme.get('info'), 'KAPATILDI': self.theme.get('success')}
        durum_lbl = QLabel(durum)
        durum_lbl.setStyleSheet(f"background: {durum_colors.get(durum, '#666')}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;")
        header.addWidget(durum_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Problem özeti
        problem_card = QFrame()
        problem_card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px;")
        problem_layout = QVBoxLayout(problem_card)
        
        p_header = QHBoxLayout()
        p_header.addWidget(QLabel(f"Müşteri: {self.kayit.get('cari', '-') or '-'}"))
        p_header.addWidget(QLabel(f"Ürün: {self.kayit.get('urun', '-') or '-'}"))
        p_header.addWidget(QLabel(f"Lot: {self.kayit.get('lot', '-') or '-'}"))
        p_header.addStretch()
        problem_layout.addLayout(p_header)
        
        problem_text = QLabel(f"Problem: {(self.kayit.get('hata_tanimi', '') or '')[:200]}")
        problem_text.setWordWrap(True)
        problem_text.setStyleSheet(f"color: {self.theme.get('text_secondary')};")
        problem_layout.addWidget(problem_text)
        
        layout.addWidget(problem_card)
        
        # 8D Adımları - Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        for d_num in range(9):
            d_code, d_title, d_desc = D_ADIMLARI[d_num]
            
            adim_frame = QFrame()
            adim_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}")
            
            adim_layout = QVBoxLayout(adim_frame)
            adim_layout.setContentsMargins(16, 12, 16, 12)
            
            baslik_layout = QHBoxLayout()
            
            num_bg = self.theme.get('text_secondary')
            if d_num in self.aksiyonlar:
                all_done = all(a.get('durum') == 'TAMAMLANDI' for a in self.aksiyonlar[d_num])
                num_bg = self.theme.get('success') if all_done else self.theme.get('warning')
            
            num_lbl = QLabel(d_code)
            num_lbl.setStyleSheet(f"background: {num_bg}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            baslik_layout.addWidget(num_lbl)
            
            title_lbl = QLabel(d_title)
            title_lbl.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 14px;")
            baslik_layout.addWidget(title_lbl)
            
            baslik_layout.addStretch()
            
            btn_ekle = QPushButton("Ekle")
            btn_ekle.setFixedSize(60, 30)
            btn_ekle.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 4px; font-size: 12px;")
            btn_ekle.clicked.connect(lambda _, d=d_num: self._aksiyon_ekle(d))
            baslik_layout.addWidget(btn_ekle)
            
            adim_layout.addLayout(baslik_layout)
            
            desc_lbl = QLabel(d_desc)
            desc_lbl.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-size: 11px;")
            adim_layout.addWidget(desc_lbl)
            
            if d_num in self.aksiyonlar:
                for aksiyon in self.aksiyonlar[d_num]:
                    a_layout = QHBoxLayout()
                    
                    durum_icon = "✓" if aksiyon.get('durum') == 'TAMAMLANDI' else "○"
                    durum_color = self.theme.get('success') if aksiyon.get('durum') == 'TAMAMLANDI' else self.theme.get('warning')
                    icon_lbl = QLabel(durum_icon)
                    icon_lbl.setStyleSheet(f"color: {durum_color}; font-size: 14px;")
                    icon_lbl.setFixedWidth(20)
                    a_layout.addWidget(icon_lbl)
                    
                    a_lbl = QLabel((aksiyon.get('aciklama', '') or '')[:80])
                    a_lbl.setStyleSheet(f"color: {self.theme.get('text')};")
                    a_layout.addWidget(a_lbl, 1)
                    
                    if aksiyon.get('sorumlu'):
                        s_lbl = QLabel(aksiyon.get('sorumlu'))
                        s_lbl.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-size: 11px;")
                        a_layout.addWidget(s_lbl)
                    
                    if aksiyon.get('durum') != 'TAMAMLANDI':
                        btn_tamam = QPushButton("Tamam")
                        btn_tamam.setFixedSize(60, 28)
                        btn_tamam.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 4px; font-size: 12px;")
                        btn_tamam.clicked.connect(lambda _, aid=aksiyon['id']: self._tamamla(aid))
                        a_layout.addWidget(btn_tamam)
                    
                    adim_layout.addLayout(a_layout)
            
            scroll_layout.addWidget(adim_frame)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        
        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_kapat = QPushButton("Kapat")
        btn_kapat.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 24px;")
        btn_kapat.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat)
        
        layout.addLayout(btn_layout)
    
    def _aksiyon_ekle(self, d_adimi: int):
        """Belirli D adımına aksiyon ekle"""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"D{d_adimi} - Aksiyon Ekle")
        dlg.setMinimumSize(500, 300)
        dlg.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(QLabel(f"D{d_adimi} - {D_ADIMLARI[d_adimi][1]}"))
        
        txt_aciklama = QTextEdit()
        txt_aciklama.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        txt_aciklama.setPlaceholderText("Aksiyonu açıklayın...")
        layout.addWidget(txt_aciklama)
        
        form = QFormLayout()
        cmb_sorumlu = QComboBox()
        cmb_sorumlu.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        cmb_sorumlu.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                cmb_sorumlu.addItem(row[1], row[0])
            conn.close()
        except Exception:
            pass
        form.addRow("Sorumlu:", cmb_sorumlu)
        
        date_hedef = QDateEdit()
        date_hedef.setDate(QDate.currentDate().addDays(7))
        date_hedef.setCalendarPopup(True)
        date_hedef.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        form.addRow("Hedef Tarih:", date_hedef)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_ekle = QPushButton("✓ Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 8px 16px;")
        
        def kaydet():
            aciklama = txt_aciklama.toPlainText().strip()
            if not aciklama:
                QMessageBox.warning(dlg, "Uyarı", "Açıklama girilmelidir!")
                return
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO kalite.uygunsuzluk_aksiyonlar (
                        uuid, uygunsuzluk_id, aksiyon_tipi, d_adimi, aciklama,
                        sorumlu_id, hedef_tarih, durum, olusturma_tarihi
                    ) VALUES (NEWID(), ?, '8D', ?, ?, ?, ?, 'AÇIK', GETDATE())
                """, (self.uygunsuzluk_id, d_adimi, aciklama, cmb_sorumlu.currentData(), date_hedef.date().toPython()))
                conn.commit()
                LogManager.log_insert('kalite', 'kalite.uygunsuzluk_aksiyonlar', None, 'Uygunsuzluk kaydi olustu')
                conn.close()
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Hata", f"Kayıt başarısız: {e}")
        
        btn_ekle.clicked.connect(kaydet)
        btn_layout.addWidget(btn_ekle)
        layout.addLayout(btn_layout)
        
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
            self.close()
            new_dlg = Detay8DDialog(self.theme, self.uygunsuzluk_id, self.parent())
            new_dlg.exec()
    
    def _tamamla(self, aksiyon_id: int):
        """Aksiyonu tamamla"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE kalite.uygunsuzluk_aksiyonlar 
                SET durum = 'TAMAMLANDI', tamamlanma_tarihi = CAST(GETDATE() AS DATE)
                WHERE id = ?
            """, (aksiyon_id,))
            conn.commit()
            LogManager.log_update('kalite', 'kalite.uygunsuzluk_aksiyonlar', None, 'Durum guncellendi')
            conn.close()
            
            self._load_data()
            self.close()
            new_dlg = Detay8DDialog(self.theme, self.uygunsuzluk_id, self.parent())
            new_dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme başarısız: {e}")


class Kalite8DPage(BasePage):
    """8D / CAPA Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("✅ 8D / CAPA Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        btn_yeni = QPushButton("➕ Yeni 8D Raporu")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_8d)
        header.addWidget(btn_yeni)
        
        layout.addLayout(header)
        
        # Bilgi kartı
        info_card = QFrame()
        info_card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px;")
        info_layout = QHBoxLayout(info_card)
        info_text = QLabel("📋 8D problem çözme metodolojisi ile sistematik kök neden analizi ve düzeltici faaliyetler yönetimi.")
        info_text.setStyleSheet(f"color: {self.theme.get('text_secondary')};")
        info_layout.addWidget(info_text)
        layout.addWidget(info_card)
        
        # İstatistik kartları
        stat_layout = QHBoxLayout()
        
        self.stat_aktif = self._create_stat_card("⚡ Aktif 8D", "0", self.theme.get('warning', '#f59e0b'))
        stat_layout.addWidget(self.stat_aktif)
        
        self.stat_tamamlanan = self._create_stat_card("✅ Tamamlanan", "0", self.theme.get('success', '#22c55e'))
        stat_layout.addWidget(self.stat_tamamlanan)
        
        self.stat_geciken = self._create_stat_card("⏰ Geciken", "0", self.theme.get('danger', '#ef4444'))
        stat_layout.addWidget(self.stat_geciken)
        
        stat_layout.addStretch()
        layout.addLayout(stat_layout)
        
        # Filtre
        filtre_layout = QHBoxLayout()
        filtre_layout.addWidget(QLabel("Durum:"))
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['Tümü', 'AÇIK', 'İŞLEMDE', 'KAPATILDI'])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 6px 12px;")
        self.cmb_durum.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_durum)
        filtre_layout.addStretch()
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px;")
        btn_yenile.clicked.connect(self._load_data)
        filtre_layout.addWidget(btn_yenile)
        layout.addLayout(filtre_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Kayıt No", "Problem", "Müşteri", "Durum", "İlerleme", "Ekip Lideri", "Hedef Tarih", "İşlem"])
        self.table.setColumnWidth(8, 120)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}
            QHeaderView::section {{ background: {self.theme.get('bg_sidebar')}; color: {self.theme.get('text')}; padding: 10px; border: none; font-weight: bold; }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(160, 70)
        card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {color}; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-size: 11px;")
        layout.addWidget(lbl_title)
        lbl_value = QLabel(value)
        lbl_value.setObjectName("stat_value")
        lbl_value.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_value)
        return card
    
    def _yeni_8d(self):
        dlg = Yeni8DDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _on_double_click(self, index):
        row = index.row()
        kayit_id = int(self.table.item(row, 0).text())
        dlg = Detay8DDialog(self.theme, kayit_id, self)
        dlg.exec()
        self._load_data()
    
    def _detay_goster(self, kayit_id: int):
        dlg = Detay8DDialog(self.theme, kayit_id, self)
        dlg.exec()
        self._load_data()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            durum_filtre = self.cmb_durum.currentText()
            where_clause = "" if durum_filtre == 'Tümü' else "AND u.durum = ?"
            params = [] if durum_filtre == 'Tümü' else [durum_filtre]
            
            cursor.execute(f"""
                SELECT u.id, u.kayit_no, LEFT(u.hata_tanimi, 50), c.unvan, u.durum,
                       (SELECT COUNT(*) FROM kalite.uygunsuzluk_aksiyonlar WHERE uygunsuzluk_id = u.id AND aksiyon_tipi = '8D' AND durum = 'TAMAMLANDI'),
                       (SELECT COUNT(*) FROM kalite.uygunsuzluk_aksiyonlar WHERE uygunsuzluk_id = u.id AND aksiyon_tipi = '8D'),
                       p.ad + ' ' + p.soyad, u.hedef_kapanis_tarihi, u.kayit_tarihi
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN ik.personeller p ON u.sorumlu_id = p.id
                WHERE EXISTS (SELECT 1 FROM kalite.uygunsuzluk_aksiyonlar WHERE uygunsuzluk_id = u.id AND aksiyon_tipi = '8D') {where_clause}
                ORDER BY u.kayit_tarihi DESC
            """, params)
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem((row[3] or '')[:25]))
                
                durum = row[4] or ''
                durum_item = QTableWidgetItem(durum)
                durum_colors = {'AÇIK': self.theme.get('warning'), 'İŞLEMDE': self.theme.get('info'), 'KAPATILDI': self.theme.get('success')}
                if durum in durum_colors:
                    durum_item.setForeground(QColor(durum_colors[durum]))
                self.table.setItem(i, 4, durum_item)
                
                ilerleme = f"{row[5] or 0}/{row[6] or 0}"
                ilerleme_item = QTableWidgetItem(ilerleme)
                if row[6] and row[5] == row[6]:
                    ilerleme_item.setForeground(QColor(self.theme.get('success')))
                self.table.setItem(i, 5, ilerleme_item)
                
                self.table.setItem(i, 6, QTableWidgetItem(row[7] or ''))
                
                hedef = row[8]
                hedef_str = hedef.strftime('%d.%m.%Y') if hedef else '-'
                hedef_item = QTableWidgetItem(hedef_str)
                if hedef and hedef < date.today() and durum != 'KAPATILDI':
                    hedef_item.setForeground(QColor(self.theme.get('danger')))
                self.table.setItem(i, 7, hedef_item)
                
                widget = self.create_action_buttons([
                    ("📋", "Detay", lambda checked, kid=row[0]: self._detay_goster(kid), "info"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 42)
            
            # İstatistikler
            cursor.execute("SELECT COUNT(DISTINCT u.id) FROM kalite.uygunsuzluklar u WHERE u.durum IN ('AÇIK', 'İŞLEMDE') AND EXISTS (SELECT 1 FROM kalite.uygunsuzluk_aksiyonlar WHERE uygunsuzluk_id = u.id AND aksiyon_tipi = '8D')")
            self.stat_aktif.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("SELECT COUNT(DISTINCT u.id) FROM kalite.uygunsuzluklar u WHERE u.durum = 'KAPATILDI' AND EXISTS (SELECT 1 FROM kalite.uygunsuzluk_aksiyonlar WHERE uygunsuzluk_id = u.id AND aksiyon_tipi = '8D')")
            self.stat_tamamlanan.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("SELECT COUNT(DISTINCT u.id) FROM kalite.uygunsuzluklar u WHERE u.durum IN ('AÇIK', 'İŞLEMDE') AND u.hedef_kapanis_tarihi < CAST(GETDATE() AS DATE) AND EXISTS (SELECT 1 FROM kalite.uygunsuzluk_aksiyonlar WHERE uygunsuzluk_id = u.id AND aksiyon_tipi = '8D')")
            self.stat_geciken.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
