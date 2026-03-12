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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEXOR ERP — Giriş")
        # RFID varsa biraz daha yüksek
        h = 600 if RFID_LOGIN_ENABLED else 520
        self.setFixedSize(440, h)
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
        outer.setContentsMargins(20, 20, 20, 20)

        # Ana kart
        card = QFrame()
        card.setObjectName("loginCard")
        card.setStyleSheet("""
            #loginCard {
                background: #1A1A2E;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 36)
        layout.setSpacing(0)

        # ── Üst kırmızı accent çizgi ──
        accent = QFrame()
        accent.setFixedHeight(3)
        accent.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #E2130D, stop:1 #FF4136);
            border-radius: 1px;
        """)
        layout.addWidget(accent)
        layout.addSpacing(28)

        # ── REDLINE / NEXOR / ERP YÖNETİM SİSTEMLERİ ──
        redline = QLabel("REDLINE")
        redline.setAlignment(Qt.AlignCenter)
        redline.setStyleSheet("color: #718096; font-size: 11px; letter-spacing: 3px;")
        layout.addWidget(redline)

        nexor = QLabel("NEXOR")
        nexor.setAlignment(Qt.AlignCenter)
        nexor.setStyleSheet("color: #E8E8E8; font-size: 30px; font-weight: bold;")
        layout.addWidget(nexor)

        subtitle = QLabel("ERP YÖNETİM SİSTEMLERİ")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #E2130D; font-size: 10px; letter-spacing: 2px; font-weight: 600;")
        layout.addWidget(subtitle)
        layout.addSpacing(32)

        # ── RFID Kart Okuyucu Bölümü ──
        if RFID_LOGIN_ENABLED:
            self.lbl_rfid_status = QLabel("\U0001F4B3  Kartınızı okutunuz...")
            self.lbl_rfid_status.setAlignment(Qt.AlignCenter)
            self.lbl_rfid_status.setStyleSheet("""
                color: #718096;
                font-size: 13px;
                letter-spacing: 0.5px;
                padding: 8px 0;
            """)
            layout.addWidget(self.lbl_rfid_status)
            layout.addSpacing(12)

            # "VEYA" ayırıcı
            veya_layout = QHBoxLayout()
            veya_line_left = QFrame()
            veya_line_left.setFixedHeight(1)
            veya_line_left.setStyleSheet("background: rgba(255,255,255,0.08);")
            veya_layout.addWidget(veya_line_left)

            veya_label = QLabel("VEYA")
            veya_label.setAlignment(Qt.AlignCenter)
            veya_label.setStyleSheet("""
                color: #4A5568; font-size: 10px;
                letter-spacing: 2px; font-weight: 600;
                padding: 0 16px;
            """)
            veya_layout.addWidget(veya_label)

            veya_line_right = QFrame()
            veya_line_right.setFixedHeight(1)
            veya_line_right.setStyleSheet("background: rgba(255,255,255,0.08);")
            veya_layout.addWidget(veya_line_right)

            layout.addLayout(veya_layout)
            layout.addSpacing(16)

        # ── Kullanıcı Adı ──
        user_label = QLabel("KULLANICI ADI")
        user_label.setStyleSheet("""
            color: #718096; font-size: 10px;
            font-weight: 600; letter-spacing: 1px;
        """)
        layout.addWidget(user_label)
        layout.addSpacing(6)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanıcı adınızı girin")
        self.username.setStyleSheet(self._input_style())
        self.username.setFixedHeight(44)
        layout.addWidget(self.username)
        layout.addSpacing(16)

        # ── Şifre ──
        pass_label = QLabel("ŞİFRE")
        pass_label.setStyleSheet("""
            color: #718096; font-size: 10px;
            font-weight: 600; letter-spacing: 1px;
        """)
        layout.addWidget(pass_label)
        layout.addSpacing(6)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Şifrenizi girin")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(self._input_style())
        self.password.setFixedHeight(44)
        self.password.returnPressed.connect(self._on_login)
        layout.addWidget(self.password)
        layout.addSpacing(12)

        # ── Beni hatırla ──
        self.remember_cb = QCheckBox("Beni hatırla")
        self.remember_cb.setStyleSheet("""
            QCheckBox {
                color: #A0AEC0;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 4px;
                background: rgba(255,255,255,0.05);
            }
            QCheckBox::indicator:checked {
                background: #E2130D;
                border-color: #E2130D;
            }
        """)
        layout.addWidget(self.remember_cb)
        layout.addSpacing(20)

        # ── Hata mesajı ──
        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet("color: #E2130D; font-size: 12px;")
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)
        layout.addSpacing(8)

        # ── Giriş butonu ──
        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setFixedHeight(44)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #E2130D;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #FF2D20;
            }
            QPushButton:pressed {
                background: #C20F0A;
            }
            QPushButton:disabled {
                background: #2D3748;
                color: #4A5568;
            }
        """)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        layout.addStretch()

        # ── Footer ──
        version_lbl = QLabel(f"v{VERSION}")
        version_lbl.setAlignment(Qt.AlignCenter)
        version_lbl.setStyleSheet("color: #2D3748; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(version_lbl)
        layout.addSpacing(4)

        footer = QLabel("Powered by <span style='color: #E2130D;'>Redline Creative Solutions</span>")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #4A5568; font-size: 9px;")
        layout.addWidget(footer)

        outer.addWidget(card)

        # Enter ile username → password'a geç
        self.username.returnPressed.connect(lambda: self.password.setFocus())
        self.username.setFocus()

    def _input_style(self):
        return """
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                color: #E8E8E8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #E2130D;
            }
            QLineEdit::placeholder {
                color: #4A5568;
            }
        """

    # ------------------------------------------------------------------
    # RFID Kart ile Giriş
    # ------------------------------------------------------------------

    def _on_card_reading(self, reading: bool):
        """Kart okuma durumu değiştiğinde UI güncelle."""
        if not RFID_LOGIN_ENABLED or not hasattr(self, 'lbl_rfid_status'):
            return
        if reading:
            self.lbl_rfid_status.setText("\U0001F4B3  Kart okunuyor...")
            self.lbl_rfid_status.setStyleSheet("""
                color: #E2130D;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 0.5px;
                padding: 8px 0;
            """)
        else:
            self.lbl_rfid_status.setText("\U0001F4B3  Kartınızı okutunuz...")
            self.lbl_rfid_status.setStyleSheet("""
                color: #718096;
                font-size: 13px;
                letter-spacing: 0.5px;
                padding: 8px 0;
            """)

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
        except:
            pass

    # ------------------------------------------------------------------
    # Kullanıcı Adı / Şifre ile Giriş
    # ------------------------------------------------------------------

    def _on_login(self):
        """Giriş işlemi"""
        username = self.username.text().strip()
        password = self.password.text()

        if not username or not password:
            self._show_error("Kullanıcı adı ve şifre gerekli!")
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
        except:
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
