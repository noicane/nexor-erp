"""
NEXOR - Bana Atanan Aksiyonlar Modülü
Geliştirici: Muhammed / Redline Creative Solutions
Framework: PySide6
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor
from typing import Optional, List, Dict, Any

from components.base_page import BasePage
from core.database import execute_query
from core.yetki_manager import YetkiManager


class AksiyonBanaAtanan(BasePage):
    """Bana atanan aksiyonları gösteren sayfa"""

    aksiyon_clicked = Signal(int)  # aksiyon_id

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.personel_id: Optional[int] = None
        self.aksiyonlar: List[Dict[str, Any]] = []

        self._init_ui()
        # YetkiManager henuz hazir olmayabilir, QTimer ile ertele
        QTimer.singleShot(100, self._deferred_load)

    def _init_ui(self):
        """Arayüz bileşenlerini oluştur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Başlık
        title = self.create_section_title("Bana Atanan Aksiyonlar")
        main_layout.addWidget(title)

        # Üst kısım: İstatistik kartları
        stats_layout = self._create_stats_section()
        main_layout.addLayout(stats_layout)

        # Filtreler
        filter_layout = self._create_filter_section()
        main_layout.addLayout(filter_layout)

        # Aksiyonlar scroll alanı
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area, 1)

    def _deferred_load(self):
        """YetkiManager hazir olduktan sonra verileri yukle"""
        self._load_user_info()
        if self.personel_id:
            self._load_data()
        else:
            user_id = YetkiManager._current_user_id
            self._show_empty_message(
                f"Personel kaydı bulunamadı.\n"
                f"(Kullanıcı ID: {user_id}, Personel ID: {self.personel_id})\n"
                f"Kullanıcı hesabınız bir personel kaydına bağlı olmayabilir."
            )

    def _open_detay(self, aksiyon_id: int):
        """Aksiyon detay dialog'unu ac"""
        from modules.aksiyonlar.aksiyon_detay_dialog import AksiyonDetayDialog
        dialog = AksiyonDetayDialog(self.theme, aksiyon_id=aksiyon_id, parent=self)
        if dialog.exec():
            self._load_data()

    def _create_stats_section(self) -> QHBoxLayout:
        """İstatistik kartları oluştur"""
        layout = QHBoxLayout()
        layout.setSpacing(16)

        self.stat_toplam = self._create_stat_card("Bana Atanan", "0", "#3b82f6")
        self.stat_bekleyen = self._create_stat_card("Bekleyen", "0", "#6b7280")
        self.stat_devam = self._create_stat_card("Devam Eden", "0", "#f59e0b")
        self.stat_geciken = self._create_stat_card("Geciken", "0", "#ef4444")

        layout.addWidget(self.stat_toplam)
        layout.addWidget(self.stat_bekleyen)
        layout.addWidget(self.stat_devam)
        layout.addWidget(self.stat_geciken)

        return layout

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Tek bir istatistik kartı oluştur"""
        t = self.theme
        card = QFrame()
        card.setMinimumHeight(100)
        card.setStyleSheet(f"""
            QFrame {{
                background: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 14px;
                padding: 20px;
            }}
            QFrame:hover {{
                border-color: {color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 13px; border: none;")
        layout.addWidget(title_label)

        # Değer
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700; border: none;")
        layout.addWidget(value_label)

        layout.addStretch()

        # Karta referansı sakla
        card.value_label = value_label

        return card

    def _create_filter_section(self) -> QHBoxLayout:
        """Filtre bölümü oluştur"""
        layout = QHBoxLayout()
        layout.setSpacing(12)

        # Durum filtresi
        durum_label = QLabel("Durum:")
        layout.addWidget(durum_label)

        self.durum_combo = QComboBox()
        self.durum_combo.setMinimumWidth(150)
        self.durum_combo.addItem("Tümü", None)
        self.durum_combo.addItem("Bekleyen", "BEKLIYOR")
        self.durum_combo.addItem("Devam Eden", "DEVAM_EDIYOR")
        self.durum_combo.addItem("Geciken", "GECIKTI")
        self.durum_combo.addItem("Tamamlanan", "TAMAMLANDI")
        self.durum_combo.addItem("Doğrulanan", "DOGRULANDI")
        self.durum_combo.addItem("İptal", "IPTAL")
        self.durum_combo.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.durum_combo)

        # Öncelik filtresi
        oncelik_label = QLabel("Öncelik:")
        layout.addWidget(oncelik_label)

        self.oncelik_combo = QComboBox()
        self.oncelik_combo.setMinimumWidth(150)
        self.oncelik_combo.addItem("Tümü", None)
        self.oncelik_combo.addItem("Düşük", "DUSUK")
        self.oncelik_combo.addItem("Normal", "NORMAL")
        self.oncelik_combo.addItem("Yüksek", "YUKSEK")
        self.oncelik_combo.addItem("Kritik", "KRITIK")
        self.oncelik_combo.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.oncelik_combo)

        layout.addStretch()

        # Yenile butonu
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setMinimumWidth(100)
        refresh_btn.clicked.connect(self._deferred_load)
        layout.addWidget(refresh_btn)

        return layout

    def _load_user_info(self):
        """Mevcut kullanıcının personel_id'sini yükle (fallback ile)"""
        try:
            user_id = YetkiManager._current_user_id
            if not user_id:
                print("[AksiyonBanaAtanan] YetkiManager._current_user_id bos!")
                return

            query = "SELECT personel_id, ad, soyad, email FROM sistem.kullanicilar WHERE id = ?"
            result = execute_query(query, (user_id,))

            if not result or len(result) == 0:
                print(f"[AksiyonBanaAtanan] Kullanici {user_id} bulunamadi!")
                return

            user = result[0]
            self.personel_id = user.get('personel_id')

            if self.personel_id:
                print(f"[AksiyonBanaAtanan] user_id={user_id}, personel_id={self.personel_id}")
                return

            # Fallback 1: ad + soyad ile personel tablosunda ara
            ad = user.get('ad')
            soyad = user.get('soyad')
            if ad and soyad:
                fallback_query = """
                    SELECT id FROM ik.personeller
                    WHERE ad = ? AND soyad = ? AND aktif_mi = 1 AND silindi_mi = 0
                """
                fb_result = execute_query(fallback_query, (ad, soyad))
                if fb_result and len(fb_result) == 1:
                    self.personel_id = fb_result[0]['id']
                    print(f"[AksiyonBanaAtanan] Fallback (ad+soyad) ile eslestirildi: "
                          f"user_id={user_id}, personel_id={self.personel_id}")
                    return

            # Fallback 2: email ile personel tablosunda ara
            email = user.get('email')
            if email:
                fallback_query = """
                    SELECT id FROM ik.personeller
                    WHERE email = ? AND aktif_mi = 1 AND silindi_mi = 0
                """
                fb_result = execute_query(fallback_query, (email,))
                if fb_result and len(fb_result) == 1:
                    self.personel_id = fb_result[0]['id']
                    print(f"[AksiyonBanaAtanan] Fallback (email) ile eslestirildi: "
                          f"user_id={user_id}, personel_id={self.personel_id}")
                    return

            print(f"[AksiyonBanaAtanan] UYARI: Kullanici {user_id} ({ad} {soyad}) icin "
                  f"personel eslesmesi bulunamadi!")

        except Exception as e:
            print(f"[AksiyonBanaAtanan] Kullanici bilgisi yuklenirken hata: {e}")

    def _show_empty_message(self, message: str):
        """Bos durum mesaji goster"""
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 14px; padding: 40px;")
        self.cards_layout.insertWidget(0, msg_label)

    def _load_data(self):
        """Bana atanan aksiyonları yükle"""
        if not self.personel_id:
            # personel_id olmadan yeniden dene
            self._load_user_info()
            if not self.personel_id:
                self._show_empty_message(
                    "Personel kaydı bulunamadı. Kullanıcı hesabınız bir personel kaydına bağlı olmayabilir."
                )
                return

        try:
            query = """
                SELECT
                    id AS aksiyon_id,
                    aksiyon_no,
                    baslik,
                    kategori,
                    oncelik,
                    durum,
                    hedef_tarih,
                    tamamlanma_orani,
                    gecikme_gun,
                    kalan_gun,
                    sorumlu_adi
                FROM sistem.vw_aksiyon_ozet
                WHERE sorumlu_id = ?
                ORDER BY
                    CASE oncelik
                        WHEN 'KRITIK' THEN 1
                        WHEN 'YUKSEK' THEN 2
                        WHEN 'NORMAL' THEN 3
                        WHEN 'DUSUK' THEN 4
                    END,
                    hedef_tarih ASC
            """

            self.aksiyonlar = execute_query(query, (self.personel_id,)) or []
            print(f"[AksiyonBanaAtanan] personel_id={self.personel_id} icin {len(self.aksiyonlar)} aksiyon bulundu")

            if len(self.aksiyonlar) == 0:
                # Debug: toplam aksiyon sayisini kontrol et
                try:
                    total = execute_query("SELECT COUNT(*) AS cnt FROM sistem.vw_aksiyon_ozet")
                    total_cnt = total[0]['cnt'] if total else '?'
                    by_user = execute_query(
                        "SELECT TOP 3 sorumlu_id, sorumlu_adi FROM sistem.vw_aksiyon_ozet",
                    )
                    sorumlu_info = ', '.join(
                        [f"{r.get('sorumlu_adi','?')}(id:{r.get('sorumlu_id','?')})" for r in (by_user or [])]
                    )
                except Exception:
                    total_cnt = '?'
                    sorumlu_info = '?'
                self._show_empty_message(
                    f"Size atanmış aksiyon bulunamadı.\n"
                    f"(Personel ID: {self.personel_id} | Toplam aksiyon: {total_cnt})\n"
                    f"(Mevcut sorumlular: {sorumlu_info})"
                )
                return

            self._update_stats()
            self._apply_filters()

        except Exception as e:
            print(f"[AksiyonBanaAtanan] Aksiyonlar yuklenirken hata: {e}")

    def _update_stats(self):
        """İstatistikleri güncelle"""
        toplam = len(self.aksiyonlar)
        bekleyen = sum(1 for a in self.aksiyonlar if a['durum'] == 'BEKLIYOR')
        devam = sum(1 for a in self.aksiyonlar if a['durum'] == 'DEVAM_EDIYOR')
        geciken = sum(1 for a in self.aksiyonlar if a['durum'] == 'GECIKTI')

        self.stat_toplam.value_label.setText(str(toplam))
        self.stat_bekleyen.value_label.setText(str(bekleyen))
        self.stat_devam.value_label.setText(str(devam))
        self.stat_geciken.value_label.setText(str(geciken))

    def _apply_filters(self):
        """Filtreleri uygula ve kartları göster"""
        # Mevcut kartları temizle
        while self.cards_layout.count() > 1:  # Son stretch hariç
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filtre değerlerini al
        durum_filter = self.durum_combo.currentData()
        oncelik_filter = self.oncelik_combo.currentData()

        # Filtrelenmiş aksiyonları göster
        filtered_count = 0
        for aksiyon in self.aksiyonlar:
            # Durum filtresi
            if durum_filter and aksiyon['durum'] != durum_filter:
                continue

            # Öncelik filtresi
            if oncelik_filter and aksiyon['oncelik'] != oncelik_filter:
                continue

            card = self._create_aksiyon_card(aksiyon)
            self.cards_layout.insertWidget(filtered_count, card)
            filtered_count += 1

        # Sonuç yoksa mesaj göster
        if filtered_count == 0:
            no_result = QLabel("Filtrelere uygun aksiyon bulunamadı")
            no_result.setAlignment(Qt.AlignCenter)
            no_result.setStyleSheet("color: #666666; font-size: 14px; padding: 40px;")
            self.cards_layout.insertWidget(0, no_result)

    def _create_aksiyon_card(self, aksiyon: Dict[str, Any]) -> QFrame:
        """Aksiyon kartı oluştur"""
        t = self.theme
        card = QFrame()
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(140)
        card.setStyleSheet(f"""
            QFrame {{
                background: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {t['primary']};
            }}
        """)

        # Kart tiklanabilir - detay dialog ac
        card.mousePressEvent = lambda event, aid=aksiyon['aksiyon_id']: self._open_detay(aid)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Üst satır: Aksiyon no + Badge'ler
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Aksiyon no
        no_label = QLabel(f"#{aksiyon['aksiyon_no']}")
        no_label.setStyleSheet(f"color: {t['primary']}; border: none;")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        no_label.setFont(font)
        top_row.addWidget(no_label)

        # Kategori badge
        if aksiyon['kategori']:
            kategori_badge = self._create_badge(aksiyon['kategori'], "#6b7280")
            top_row.addWidget(kategori_badge)

        # Öncelik badge
        oncelik_color = self._get_oncelik_color(aksiyon['oncelik'])
        oncelik_text = self._get_oncelik_text(aksiyon['oncelik'])
        oncelik_badge = self._create_badge(oncelik_text, oncelik_color)
        top_row.addWidget(oncelik_badge)

        # Durum badge
        durum_color = self._get_durum_color(aksiyon['durum'])
        durum_text = self._get_durum_text(aksiyon['durum'])
        durum_badge = self._create_badge(durum_text, durum_color)
        top_row.addWidget(durum_badge)

        top_row.addStretch()
        layout.addLayout(top_row)

        # Başlık
        baslik_label = QLabel(aksiyon['baslik'])
        baslik_label.setStyleSheet(f"color: {t['text']}; border: none;")
        baslik_label.setWordWrap(True)
        baslik_label.setMaximumHeight(40)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        baslik_label.setFont(font)
        layout.addWidget(baslik_label)

        # Alt satır: Tarih bilgileri ve ilerleme
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Hedef tarih
        hedef_tarih_str = "Belirtilmemiş"
        if aksiyon['hedef_tarih']:
            hedef_tarih_str = aksiyon['hedef_tarih'].strftime("%d.%m.%Y")

        tarih_label = QLabel(f"Hedef: {hedef_tarih_str}")
        tarih_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 10px; border: none;")
        bottom_row.addWidget(tarih_label)

        # Kalan/Geciken gün
        if aksiyon['kalan_gun'] is not None:
            if aksiyon['kalan_gun'] >= 0:
                gun_label = QLabel(f"{aksiyon['kalan_gun']} gün kaldı")
                gun_label.setStyleSheet("color: #10b981;")
            else:
                gun_label = QLabel(f"{abs(aksiyon['kalan_gun'])} gün gecikti")
                gun_label.setStyleSheet("color: #ef4444;")
            bottom_row.addWidget(gun_label)

        bottom_row.addStretch()

        # Tamamlanma oranı
        oran = aksiyon['tamamlanma_orani'] or 0
        oran_label = QLabel(f"%{oran}")
        oran_label.setStyleSheet(f"color: {t['text']}; border: none;")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        oran_label.setFont(font)
        bottom_row.addWidget(oran_label)

        layout.addLayout(bottom_row)

        # İlerleme çubuğu
        progress_bar = self._create_progress_bar(oran)
        layout.addWidget(progress_bar)

        return card

    def _create_badge(self, text: str, color: str) -> QLabel:
        """Badge etiketi oluştur"""
        badge = QLabel(text)
        badge.setObjectName("badge")
        badge.setStyleSheet(f"""
            QLabel#badge {{
                background-color: {color};
                color: #FFFFFF;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 9px;
                font-weight: bold;
            }}
        """)
        return badge

    def _create_progress_bar(self, percentage: int) -> QFrame:
        """İlerleme çubuğu oluştur"""
        container = QFrame()
        container.setFixedHeight(6)
        container.setStyleSheet("background-color: #2a2a2a; border-radius: 3px;")

        progress = QFrame(container)
        progress.setFixedHeight(6)

        # Renk seçimi
        if percentage >= 75:
            color = "#10b981"  # Yeşil
        elif percentage >= 50:
            color = "#f59e0b"  # Turuncu
        elif percentage >= 25:
            color = "#3b82f6"  # Mavi
        else:
            color = "#6b7280"  # Gri

        progress.setStyleSheet(f"""
            background-color: {color};
            border-radius: 3px;
        """)

        # Genislik hesaplamasini resizeEvent ile yap
        pct = percentage

        def _update_width():
            w = container.width()
            if w > 0:
                progress.setFixedWidth(max(0, int(w * pct / 100)))

        original_resize = container.resizeEvent

        def _on_resize(event):
            if original_resize:
                original_resize(event)
            _update_width()

        container.resizeEvent = _on_resize
        # Ilk cizim icin de bir timer koy
        QTimer.singleShot(100, _update_width)

        return container

    def _get_durum_color(self, durum: str) -> str:
        """Durum rengini döndür"""
        colors = {
            'BEKLIYOR': '#3b82f6',
            'DEVAM_EDIYOR': '#f59e0b',
            'TAMAMLANDI': '#10b981',
            'DOGRULANDI': '#10b981',
            'GECIKTI': '#ef4444',
            'IPTAL': '#666666'
        }
        return colors.get(durum, '#6b7280')

    def _get_durum_text(self, durum: str) -> str:
        """Durum metnini döndür"""
        texts = {
            'BEKLIYOR': 'Bekleyen',
            'DEVAM_EDIYOR': 'Devam Ediyor',
            'TAMAMLANDI': 'Tamamlandı',
            'DOGRULANDI': 'Doğrulandı',
            'GECIKTI': 'Gecikti',
            'IPTAL': 'İptal'
        }
        return texts.get(durum, durum)

    def _get_oncelik_color(self, oncelik: str) -> str:
        """Öncelik rengini döndür"""
        colors = {
            'DUSUK': '#6b7280',
            'NORMAL': '#3b82f6',
            'YUKSEK': '#f59e0b',
            'KRITIK': '#ef4444'
        }
        return colors.get(oncelik, '#6b7280')

    def _get_oncelik_text(self, oncelik: str) -> str:
        """Öncelik metnini döndür"""
        texts = {
            'DUSUK': 'Düşük',
            'NORMAL': 'Normal',
            'YUKSEK': 'Yüksek',
            'KRITIK': 'Kritik'
        }
        return texts.get(oncelik, oncelik)

