# -*- coding: utf-8 -*-
"""
REDLINE NEXOR - Login Dialog
PRAXIS tarzı kurumsal giriş ekranı + RFID/NFC kart ile giriş desteği
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QEvent
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor
import hashlib

from core.database import get_db_connection
from core.log_manager import LogManager
from core.yetki_manager import YetkiManager
from core.rfid_reader import RFIDCardReader
from core.nexor_brand import brand
from config import RFID_LOGIN_ENABLED
from version import VERSION


def get_icon_path() -> str:
    """Icon dosyasının yolunu döndürür"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent

    icon_path = base_path / "assets" / "icon.ico"
    return str(icon_path) if icon_path.exists() else ""


class NexorLoginDialog(QDialog):
    """Redline Nexor Login Dialog - PRAXIS Kurumsal Stil"""

    # Giriş yapan kullanıcı bilgileri
    current_user_id = None
    current_user_name = None
    current_user_fullname = None
    current_user_role = None
    current_user_role_id = None
    # master/008384 girilirse True olur; main.py NEXOR yerine bayi panelini açar
    master_mode = False

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEXOR ERP — Giriş")
        # Boyut scale'e gore responsive
        w = brand.sp(480)
        h = brand.sp(620 if RFID_LOGIN_ENABLED else 540)
        self.setFixedSize(w, h)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Window icon ayarla
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # RFID kart okuyucu
        self._rfid_reader = RFIDCardReader(self)
        self._rfid_reader.set_active(RFID_LOGIN_ENABLED)
        self._rfid_reader.card_detected.connect(self._on_card_detected)
        self._rfid_reader.card_reading.connect(self._on_card_reading)

        self._setup_ui()

        # Event filter - dialog seviyesinde ve QLineEdit'lerden tuş vuruşlarını yakala
        if RFID_LOGIN_ENABLED:
            self.username.installEventFilter(self)
            self.password.installEventFilter(self)
            # Dialog seviyesinde de yakala (focus nerede olursa olsun)
            self.installEventFilter(self)

        # Animasyon ekle
        QTimer.singleShot(100, self._animate_entrance)

    def _animate_entrance(self):
        """Giriş animasyonu"""
        self.setWindowOpacity(0)
        self.show()

        self.fade_in = QPropertyAnimation(self.windowHandle(), b"opacity")
        self.fade_in.setDuration(400)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in.start()

    def eventFilter(self, watched, event):
        """QLineEdit'lerden gelen tuş vuruşlarını RFID okuyucuya yönlendir."""
        if event.type() == QEvent.Type.KeyPress:
            if self._rfid_reader.process_key(event):
                return True
        return super().eventFilter(watched, event)

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(brand.sp(16), brand.sp(16), brand.sp(16), brand.sp(16))

        # ========== ANA KART ==========
        card = QFrame()
        card.setObjectName("loginCard")
        card.setStyleSheet(f"""
            QFrame#loginCard {{
                background: {brand.BG_ELEVATED};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_XL}px;
            }}
            QFrame#loginCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            brand.SP_10, brand.sp(36), brand.SP_10, brand.SP_8
        )
        layout.setSpacing(0)

        # ---------- ÜST KIRMIZI ACCENT ÇİZGİ ----------
        accent = QFrame()
        accent.setFixedHeight(brand.sp(3))
        accent.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {brand.PRIMARY}, stop:1 #FF4136);
            border: none; border-radius: 1px;
        """)
        layout.addWidget(accent)
        layout.addSpacing(brand.SP_8)

        # ---------- LOGO / MARKA ----------
        redline = QLabel("REDLINE")
        redline.setAlignment(Qt.AlignCenter)
        redline.setStyleSheet(
            f"color: {brand.TEXT_DIM}; "
            f"font-size: {brand.FS_CAPTION}px; "
            f"letter-spacing: 4px; font-weight: {brand.FW_MEDIUM};"
        )
        layout.addWidget(redline)

        layout.addSpacing(brand.SP_1)

        nexor = QLabel("NEXOR")
        nexor.setAlignment(Qt.AlignCenter)
        nexor.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.fs(36)}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"letter-spacing: -0.5px;"
        )
        layout.addWidget(nexor)

        subtitle = QLabel("ERP YÖNETİM SİSTEMLERİ")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {brand.PRIMARY}; "
            f"font-size: {brand.fs(10)}px; "
            f"letter-spacing: 3px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        layout.addWidget(subtitle)
        layout.addSpacing(brand.SP_8)

        # ---------- RFID BÖLÜMÜ ----------
        if RFID_LOGIN_ENABLED:
            rfid_box = QFrame()
            rfid_box.setObjectName("rfidBox")
            rfid_box.setStyleSheet(f"""
                QFrame#rfidBox {{
                    background: {brand.BG_INPUT};
                    border: 1px dashed {brand.BORDER_HARD};
                    border-radius: {brand.R_MD}px;
                }}
                QFrame#rfidBox QLabel {{ background: transparent; border: none; }}
            """)
            rfid_lay = QVBoxLayout(rfid_box)
            rfid_lay.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
            rfid_lay.setSpacing(brand.SP_1)

            self.lbl_rfid_status = QLabel("Kartınızı okuyucuya yaklaştırın")
            self.lbl_rfid_status.setAlignment(Qt.AlignCenter)
            self.lbl_rfid_status.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; "
                f"font-size: {brand.FS_BODY_SM}px; "
                f"font-weight: {brand.FW_MEDIUM};"
            )
            rfid_lay.addWidget(self.lbl_rfid_status)

            rfid_hint = QLabel("Kart ile hızlı giriş")
            rfid_hint.setAlignment(Qt.AlignCenter)
            rfid_hint.setStyleSheet(
                f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
            )
            rfid_lay.addWidget(rfid_hint)

            layout.addWidget(rfid_box)
            layout.addSpacing(brand.SP_4)

            # "VEYA" ayırıcı
            veya_layout = QHBoxLayout()
            veya_layout.setSpacing(brand.SP_3)
            line_left = QFrame()
            line_left.setFixedHeight(1)
            line_left.setStyleSheet(f"background: {brand.BORDER};")
            veya_layout.addWidget(line_left, 1)

            veya_label = QLabel("VEYA")
            veya_label.setAlignment(Qt.AlignCenter)
            veya_label.setStyleSheet(
                f"color: {brand.TEXT_DIM}; "
                f"font-size: {brand.fs(10)}px; "
                f"letter-spacing: 2px; "
                f"font-weight: {brand.FW_SEMIBOLD};"
            )
            veya_layout.addWidget(veya_label)

            line_right = QFrame()
            line_right.setFixedHeight(1)
            line_right.setStyleSheet(f"background: {brand.BORDER};")
            veya_layout.addWidget(line_right, 1)

            layout.addLayout(veya_layout)
            layout.addSpacing(brand.SP_4)

        # ---------- KULLANICI ADI ----------
        user_label = QLabel("KULLANICI ADI")
        user_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.fs(10)}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"letter-spacing: 1.2px;"
        )
        layout.addWidget(user_label)
        layout.addSpacing(brand.SP_2)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanıcı adınızı girin")
        self.username.setStyleSheet(self._input_style())
        self.username.setFixedHeight(brand.sp(44))
        layout.addWidget(self.username)
        layout.addSpacing(brand.SP_4)

        # ---------- ŞİFRE ----------
        pass_label = QLabel("ŞİFRE")
        pass_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.fs(10)}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"letter-spacing: 1.2px;"
        )
        layout.addWidget(pass_label)
        layout.addSpacing(brand.SP_2)

        self.password = QLineEdit()
        self.password.setPlaceholderText("••••••••")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(self._input_style())
        self.password.setFixedHeight(brand.sp(44))
        self.password.returnPressed.connect(self._on_login)
        layout.addWidget(self.password)
        layout.addSpacing(brand.SP_3)

        # ---------- BENİ HATIRLA ----------
        self.remember_cb = QCheckBox("Beni hatırla")
        self.remember_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {brand.TEXT_MUTED};
                font-size: {brand.FS_BODY_SM}px;
                spacing: {brand.SP_2}px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: {brand.sp(16)}px;
                height: {brand.sp(16)}px;
                border: 1px solid {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                background: {brand.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                background: {brand.PRIMARY};
                border-color: {brand.PRIMARY};
                image: none;
            }}
            QCheckBox::indicator:hover {{
                border-color: {brand.PRIMARY};
            }}
        """)
        layout.addWidget(self.remember_cb)
        layout.addSpacing(brand.SP_3)

        # ---------- HATA MESAJI ----------
        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet(
            f"color: {brand.ERROR}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px; "
            f"background: {brand.ERROR_SOFT}; "
            f"border: 1px solid rgba(239,68,68,0.25); "
            f"border-radius: {brand.R_SM}px;"
        )
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)
        layout.addSpacing(brand.SP_3)

        # ---------- GİRİŞ BUTONU ----------
        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setFixedHeight(brand.sp(46))
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_MD}px;
                font-size: {brand.FS_BODY_LG}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: #E43737;
            }}
            QPushButton:pressed {{
                background: {brand.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_DISABLED};
            }}
        """)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        layout.addStretch()

        # ---------- FOOTER ----------
        version_lbl = QLabel(f"v{VERSION}")
        version_lbl.setAlignment(Qt.AlignCenter)
        version_lbl.setStyleSheet(
            f"color: {brand.TEXT_DISABLED}; "
            f"font-size: {brand.fs(10)}px; "
            f"letter-spacing: 1px;"
        )
        layout.addWidget(version_lbl)
        layout.addSpacing(brand.SP_1)

        footer = QLabel(
            f"Powered by <span style='color: {brand.PRIMARY};'>"
            f"Redline Creative Solutions</span>"
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.fs(9)}px;"
        )
        layout.addWidget(footer)

        outer.addWidget(card)

        # Enter ile username → password'a geç
        self.username.returnPressed.connect(lambda: self.password.setFocus())

        # ---------- BENİ HATIRLA YÜKLEME ----------
        self._load_remembered()

    def _input_style(self):
        return f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_3}px {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                selection-background-color: {brand.PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {brand.PRIMARY};
                background: {brand.BG_HOVER};
            }}
            QLineEdit:hover:!focus {{
                border-color: {brand.BORDER_HARD};
            }}
        """

    # ------------------------------------------------------------------
    # BENI HATIRLA
    # ------------------------------------------------------------------

    def _load_remembered(self):
        """Daha once 'Beni Hatirla' isaretlendiyse kullanici adini yukle."""
        try:
            from core.external_config import config_manager
            saved_user = config_manager.get('login.remembered_user', '')
            if saved_user:
                self.username.setText(str(saved_user))
                self.remember_cb.setChecked(True)
                self.password.setFocus()
            else:
                self.username.setFocus()
        except Exception:
            self.username.setFocus()

    def _save_remembered(self, username: str):
        """Basarili giriste kullanici adini kaydet (sifre ASLA kaydedilmez)."""
        try:
            from core.external_config import config_manager
            if self.remember_cb.isChecked():
                config_manager.set('login.remembered_user', username or '')
            else:
                config_manager.set('login.remembered_user', '')
            config_manager.save()
        except Exception as e:
            print(f"[Login] Beni hatirla kaydedilemedi: {e}")

    # ------------------------------------------------------------------
    # RFID Kart ile Giriş
    # ------------------------------------------------------------------

    def _on_card_reading(self, reading: bool):
        """Kart okuma durumu değiştiğinde UI güncelle."""
        if not RFID_LOGIN_ENABLED or not hasattr(self, 'lbl_rfid_status'):
            return
        if reading:
            self.lbl_rfid_status.setText("Kart okunuyor...")
            self.lbl_rfid_status.setStyleSheet(
                f"color: {brand.PRIMARY}; "
                f"font-size: {brand.FS_BODY_SM}px; "
                f"font-weight: {brand.FW_BOLD};"
            )
        else:
            self.lbl_rfid_status.setText("Kartınızı okuyucuya yaklaştırın")
            self.lbl_rfid_status.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; "
                f"font-size: {brand.FS_BODY_SM}px; "
                f"font-weight: {brand.FW_MEDIUM};"
            )

    def _on_card_detected(self, card_id: str):
        """Kart algılandığında kimlik doğrulama yap."""
        print(f"[RFID-LOGIN] Kart algılandı: {card_id}")
        self.username.clear()
        self.password.clear()
        self.lbl_error.hide()
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Doğrulanıyor...")

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Sorgu 1: sistem.kullanicilar tablosunda direkt kart_id araması
            cursor.execute("""
                SELECT k.id, k.kullanici_adi, k.ad, k.soyad, k.aktif_mi, k.hesap_kilitli_mi,
                       k.rol_id, r.rol_adi
                FROM sistem.kullanicilar k
                LEFT JOIN sistem.roller r ON k.rol_id = r.id
                WHERE k.kart_id = ? AND ISNULL(k.silindi_mi, 0) = 0
            """, [card_id])

            user = cursor.fetchone()

            # Sorgu 2 (Fallback): ik.personeller üzerinden kart_no/kart_id araması
            if not user:
                cursor.execute("""
                    SELECT k.id, k.kullanici_adi, k.ad, k.soyad, k.aktif_mi, k.hesap_kilitli_mi,
                           k.rol_id, r.rol_adi
                    FROM sistem.kullanicilar k
                    LEFT JOIN sistem.roller r ON k.rol_id = r.id
                    INNER JOIN ik.personeller p ON k.personel_id = p.id
                    WHERE (p.kart_no = ? OR p.kart_id = ?)
                      AND ISNULL(k.silindi_mi, 0) = 0 AND ISNULL(p.aktif_mi, 1) = 1
                """, [card_id, card_id])
                user = cursor.fetchone()

            if not user:
                self._show_error("Kart tanınmadı!")
                self._log_failed_card_login(card_id)
                return

            # Hesap kilitli mi?
            if user.hesap_kilitli_mi:
                self._show_error("Hesap kilitli! Yönetici ile iletişime geçin.")
                return

            # Hesap aktif mi?
            if not user.aktif_mi:
                self._show_error("Hesap pasif durumda!")
                return

            # Başarılı giriş
            cursor.execute("""
                UPDATE sistem.kullanicilar
                SET son_giris_tarihi = GETDATE(),
                    basarisiz_giris_sayisi = 0
                WHERE id = ?
            """, [user.id])
            conn.commit()

            # Kullanıcı bilgilerini sakla
            NexorLoginDialog.current_user_id = user.id
            NexorLoginDialog.current_user_name = user.kullanici_adi
            NexorLoginDialog.current_user_fullname = f"{user.ad or ''} {user.soyad or ''}".strip()
            NexorLoginDialog.current_user_role = user.rol_adi
            NexorLoginDialog.current_user_role_id = user.rol_id

            # Login logla
            LogManager.log_login(user.id, user.kullanici_adi, basarili=True)

            # Yetkileri yükle
            YetkiManager.set_current_user(user.id, user.rol_id)

            # Kart ile girdi - kullanici adini beni hatirla'ya yaz (isaret ediliyorsa)
            self._save_remembered(user.kullanici_adi)

            self.accept()

        except ConnectionError:
            self._show_error("Veritabanına bağlanılamadı!\nAğ bağlantınızı kontrol edin.")
        except Exception as e:
            self._show_error(f"Giriş hatası: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Giriş Yap")

    def _log_failed_card_login(self, card_id: str):
        """Başarısız kart giriş denemesini logla."""
        try:
            LogManager._current_user_name = f"CARD:{card_id}"
            LogManager._ip_address = LogManager._get_local_ip()
            LogManager.log(
                modul='sistem',
                islem='LOGIN_CARD_FAILED',
                aciklama=f'Tanınmayan kart ile giriş denemesi: {card_id}'
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Kullanıcı Adı / Şifre ile Giriş
    # ------------------------------------------------------------------

    def _master_giris(self):
        """master/008384: master_mode flag'i set eder ve dialog'u kapatir.

        main.py master_mode True ise NEXOR ana ekran yerine BayiPaneli acar.
        Yetki sistemi ve modul lisanslarindan tamamen bagimsiz calisir.
        """
        # Gelistirici modunu da ac (Musteri Yonetimi vs. icin)
        try:
            from core.modul_servisi import ModulServisi
            ModulServisi.instance().set_gelistirici_modu(True)
        except Exception:
            pass

        NexorLoginDialog.master_mode = True
        # User bilgileri bos kalir; main.py master_mode'a bakar
        NexorLoginDialog.current_user_id = None
        NexorLoginDialog.current_user_name = "master"
        NexorLoginDialog.current_user_fullname = "Master (Bayi)"
        NexorLoginDialog.current_user_role = "Master"
        NexorLoginDialog.current_user_role_id = None
        self.accept()

    def _on_login(self):
        """Giriş işlemi"""
        username = self.username.text().strip()
        password = self.password.text()

        if not username or not password:
            self._show_error("Kullanıcı adı ve şifre gerekli!")
            return

        # Gizli master girisi: gelistirici modunu acar + admin olarak otomatik giris
        if username.lower() == "master" and password == "008384":
            self._master_giris()
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Doğrulanıyor...")

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Kullanıcıyı bul
            cursor.execute("""
                SELECT k.id, k.kullanici_adi, k.ad, k.soyad, k.sifre_hash,
                       k.aktif_mi, k.hesap_kilitli_mi, k.basarisiz_giris_sayisi,
                       k.rol_id, r.rol_adi
                FROM sistem.kullanicilar k
                LEFT JOIN sistem.roller r ON k.rol_id = r.id
                WHERE k.kullanici_adi = ? AND ISNULL(k.silindi_mi, 0) = 0
            """, [username])

            user = cursor.fetchone()

            if not user:
                self._show_error("Kullanıcı bulunamadı!")
                self._log_failed_login(username)
                return

            # Hesap kilitli mi?
            if user.hesap_kilitli_mi:
                self._show_error("Hesap kilitli! Yönetici ile iletişime geçin.")
                return

            # Hesap aktif mi?
            if not user.aktif_mi:
                self._show_error("Hesap pasif durumda!")
                return

            # Şifre kontrolü
            sifre_hash = hashlib.sha256(password.encode()).hexdigest()
            sifre_dogru = False

            if user.sifre_hash:
                if user.sifre_hash == sifre_hash:
                    sifre_dogru = True
                elif user.sifre_hash.startswith('$2'):
                    try:
                        import bcrypt
                        if bcrypt.checkpw(password.encode(), user.sifre_hash.encode()):
                            sifre_dogru = True
                    except ImportError:
                        pass
                    except Exception:
                        pass

            if not sifre_dogru:
                yeni_sayi = (user.basarisiz_giris_sayisi or 0) + 1
                cursor.execute("""
                    UPDATE sistem.kullanicilar
                    SET basarisiz_giris_sayisi = ?,
                        hesap_kilitli_mi = CASE WHEN ? >= 5 THEN 1 ELSE 0 END
                    WHERE id = ?
                """, [yeni_sayi, yeni_sayi, user.id])
                conn.commit()

                if yeni_sayi >= 5:
                    self._show_error("Çok fazla başarısız deneme! Hesap kilitlendi.")
                else:
                    self._show_error(f"Hatalı şifre! ({5 - yeni_sayi} deneme hakkınız kaldı)")

                self._log_failed_login(username)
                return

            # Başarılı giriş
            cursor.execute("""
                UPDATE sistem.kullanicilar
                SET son_giris_tarihi = GETDATE(),
                    basarisiz_giris_sayisi = 0
                WHERE id = ?
            """, [user.id])
            conn.commit()

            # Kullanıcı bilgilerini sakla
            NexorLoginDialog.current_user_id = user.id
            NexorLoginDialog.current_user_name = user.kullanici_adi
            NexorLoginDialog.current_user_fullname = f"{user.ad or ''} {user.soyad or ''}".strip()
            NexorLoginDialog.current_user_role = user.rol_adi
            NexorLoginDialog.current_user_role_id = user.rol_id

            # Login logla
            LogManager.log_login(user.id, user.kullanici_adi, basarili=True)

            # Yetkileri yükle
            YetkiManager.set_current_user(user.id, user.rol_id)

            # Beni Hatirla kaydet
            self._save_remembered(user.kullanici_adi)

            self.accept()

        except ConnectionError:
            self._show_error(
                "Veritabanına bağlanılamadı!\n"
                "Ağ bağlantınızı ve sunucu ayarlarını kontrol edin."
            )
        except Exception as e:
            self._show_error(f"Giriş hatası: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Giriş Yap")

    def _show_error(self, message: str):
        """Hata mesajı göster"""
        self.lbl_error.setText(message)
        self.lbl_error.show()
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Giriş Yap")

    def _log_failed_login(self, username: str):
        """Başarısız giriş denemesini logla"""
        try:
            LogManager._current_user_name = username
            LogManager._ip_address = LogManager._get_local_ip()
            LogManager.log(
                modul='sistem',
                islem='LOGIN_FAILED',
                aciklama=f'Başarısız giriş denemesi: {username}'
            )
        except Exception:
            pass

    @classmethod
    def get_current_user(cls):
        """Aktif kullanıcı bilgisini döndür"""
        return {
            'id': cls.current_user_id,
            'username': cls.current_user_name,
            'fullname': cls.current_user_fullname,
            'role': cls.current_user_role
        }

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_pos') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)


# Alias for compatibility
ModernLoginDialog = NexorLoginDialog
