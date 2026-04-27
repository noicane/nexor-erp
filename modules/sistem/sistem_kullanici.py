# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem Kullanıcı Yönetimi
sistem.kullanicilar tablosu (rol_id direkt tabloda)
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QColor
from datetime import datetime
import hashlib

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.rfid_reader import RFIDCardReader
from core.nexor_brand import brand


class KullaniciDialog(QDialog):
    """Kullanıcı ekleme/düzenleme dialogu"""
    
    def __init__(self, parent=None, theme=None, kullanici_id=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.kullanici_id = kullanici_id
        self.setWindowTitle("Yeni Kullanıcı" if not kullanici_id else "Kullanıcı Düzenle")
        self.setMinimumSize(450, 620)
        self.setModal(True)
        self._rfid_reader = RFIDCardReader(self)
        self._rfid_reader.set_active(False)
        self._rfid_reader.card_detected.connect(self._on_card_read)
        self._rfid_reading = False
        self.setup_ui()
        self.load_roller()
        self.load_personeller()
        if kullanici_id:
            self.load_kullanici()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Temel Bilgiler
        temel_group = QGroupBox("Temel Bilgiler")
        temel_layout = QFormLayout()
        
        self.txt_kullanici_adi = QLineEdit()
        self.txt_kullanici_adi.setPlaceholderText("Kullanıcı adı...")
        temel_layout.addRow("Kullanıcı Adı:", self.txt_kullanici_adi)
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("email@sirket.com")
        temel_layout.addRow("E-posta:", self.txt_email)
        
        self.txt_ad = QLineEdit()
        self.txt_ad.setPlaceholderText("Ad...")
        temel_layout.addRow("Ad:", self.txt_ad)
        
        self.txt_soyad = QLineEdit()
        self.txt_soyad.setPlaceholderText("Soyad...")
        temel_layout.addRow("Soyad:", self.txt_soyad)
        
        self.txt_telefon = QLineEdit()
        self.txt_telefon.setPlaceholderText("0532 xxx xx xx")
        temel_layout.addRow("Telefon:", self.txt_telefon)
        
        # Rol seçimi (tek rol)
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItem("-- Rol Seçin --", None)
        temel_layout.addRow("Rol:", self.cmb_rol)
        
        # Personel seçimi
        self.cmb_personel = QComboBox()
        self.cmb_personel.addItem("-- Personel Seçin (Opsiyonel) --", None)
        temel_layout.addRow("Personel:", self.cmb_personel)
        
        temel_group.setLayout(temel_layout)
        layout.addWidget(temel_group)

        # Kart Bilgisi
        kart_group = QGroupBox("Kart Bilgisi")
        kart_layout = QHBoxLayout()

        kart_label = QLabel("Kart ID:")
        kart_layout.addWidget(kart_label)

        self.txt_kart_id = QLineEdit()
        self.txt_kart_id.setPlaceholderText("Kart okutarak atayın...")
        self.txt_kart_id.setReadOnly(True)
        kart_layout.addWidget(self.txt_kart_id)

        self.btn_kart_okut = QPushButton("Kart Okut")
        self.btn_kart_okut.setCheckable(True)
        self.btn_kart_okut.setCursor(Qt.PointingHandCursor)
        self.btn_kart_okut.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                padding: 6px 14px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background: #E2130D;
            }}
            QPushButton:hover {{ background: #2563eb; }}
            QPushButton:checked:hover {{ background: #C20F0A; }}
        """)
        self.btn_kart_okut.toggled.connect(self._toggle_kart_okuma)
        kart_layout.addWidget(self.btn_kart_okut)

        btn_kart_temizle = QPushButton("Temizle")
        btn_kart_temizle.setCursor(Qt.PointingHandCursor)
        btn_kart_temizle.clicked.connect(lambda: self.txt_kart_id.clear())
        kart_layout.addWidget(btn_kart_temizle)

        kart_group.setLayout(kart_layout)
        layout.addWidget(kart_group)

        # Şifre
        sifre_title = "Şifre" if not self.kullanici_id else "Şifre (Boş bırakılırsa değişmez)"
        sifre_group = QGroupBox(sifre_title)
        sifre_layout = QFormLayout()
        
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setEchoMode(QLineEdit.Password)
        self.txt_sifre.setPlaceholderText("Şifre...")
        sifre_layout.addRow("Şifre:", self.txt_sifre)
        
        self.txt_sifre_tekrar = QLineEdit()
        self.txt_sifre_tekrar.setEchoMode(QLineEdit.Password)
        self.txt_sifre_tekrar.setPlaceholderText("Şifre tekrar...")
        sifre_layout.addRow("Şifre Tekrar:", self.txt_sifre_tekrar)
        
        self.chk_sifre_degistir = QCheckBox("İlk girişte şifre değiştirmeye zorla")
        sifre_layout.addRow("", self.chk_sifre_degistir)
        
        sifre_group.setLayout(sifre_layout)
        layout.addWidget(sifre_group)

        # Terminal PIN (EDA51 / Android terminal icin)
        # Sadece mevcut kullanici icin (yeni olusturma sirasinda once kaydet, sonra ayarla)
        self._pin_group = QGroupBox("Terminal PIN (El Terminali / Tablet)")
        pin_layout = QHBoxLayout()
        self.lbl_pin_durum = QLabel("PIN tanimli degil")
        self.lbl_pin_durum.setStyleSheet(f"color: {brand.TEXT_DIM};")
        pin_layout.addWidget(self.lbl_pin_durum, 1)
        self.btn_pin_ayarla = QPushButton("PIN Ayarla / Degistir")
        self.btn_pin_ayarla.setCursor(Qt.PointingHandCursor)
        self.btn_pin_ayarla.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY}; color: white; padding: 6px 14px;
                border: none; border-radius: 6px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        self.btn_pin_ayarla.clicked.connect(self._terminal_pin_ayarla)
        pin_layout.addWidget(self.btn_pin_ayarla)
        self.btn_pin_sil = QPushButton("Sil")
        self.btn_pin_sil.setCursor(Qt.PointingHandCursor)
        self.btn_pin_sil.clicked.connect(self._terminal_pin_sil)
        pin_layout.addWidget(self.btn_pin_sil)
        self._pin_group.setLayout(pin_layout)
        layout.addWidget(self._pin_group)
        # Yeni kayitta gizle (kaydetmeden once kullanici_id yok)
        if not self.kullanici_id:
            self._pin_group.setVisible(False)

        # Durum
        durum_group = QGroupBox("Durum")
        durum_layout = QFormLayout()
        
        self.chk_aktif = QCheckBox("Kullanıcı aktif")
        self.chk_aktif.setChecked(True)
        durum_layout.addRow("", self.chk_aktif)
        
        self.chk_kilitli = QCheckBox("Hesap kilitli")
        durum_layout.addRow("", self.chk_kilitli)
        
        durum_group.setLayout(durum_layout)
        layout.addWidget(durum_group)
        
        # Yetkiler
        yetki_group = QGroupBox("Yetkiler")
        yetki_layout = QFormLayout()
        
        self.chk_satinalma_onay = QCheckBox("Satın Alma Onay Yetkisi")
        self.chk_satinalma_onay.setToolTip("Bu kullanıcı satın alma taleplerini onaylayabilir")
        yetki_layout.addRow("", self.chk_satinalma_onay)
        
        yetki_group.setLayout(yetki_layout)
        layout.addWidget(yetki_group)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        btn_kaydet.clicked.connect(self.kaydet)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def load_roller(self):
        """Rol listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, 
                       ISNULL(rol_kodu, kod) as kod, 
                       ISNULL(rol_adi, ad) as ad 
                FROM sistem.roller 
                WHERE ISNULL(aktif_mi, 1) = 1 
                ORDER BY ISNULL(rol_adi, ad)
            """)
            for row in cursor.fetchall():
                self.cmb_rol.addItem(f"{row.ad} ({row.kod})", row.id)
            conn.close()
        except Exception as e:
            print(f"Rol yükleme hatası: {e}")
    
    def load_personeller(self):
        """Personel listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad, soyad, sicil_no 
                FROM ik.personeller 
                WHERE ISNULL(aktif_mi, 1) = 1 
                ORDER BY ad, soyad
            """)
            for row in cursor.fetchall():
                self.cmb_personel.addItem(f"{row.ad} {row.soyad} ({row.sicil_no})", row.id)
            conn.close()
        except Exception as e:
            print(f"Personel yükleme hatası: {e}")
    
    def load_kullanici(self):
        """Mevcut kullanıcı bilgilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sistem.kullanicilar WHERE id = ?
            """, [self.kullanici_id])
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kullanici_adi.setText(row.kullanici_adi or '')
                self.txt_email.setText(row.email or '')
                self.txt_ad.setText(row.ad or '')
                self.txt_soyad.setText(row.soyad or '')
                self.txt_telefon.setText(row.telefon or '')
                self.chk_aktif.setChecked(bool(row.aktif_mi) if row.aktif_mi is not None else True)
                self.chk_kilitli.setChecked(bool(row.hesap_kilitli_mi) if row.hesap_kilitli_mi is not None else False)
                self.chk_sifre_degistir.setChecked(bool(row.sifre_degisim_gerekli) if row.sifre_degisim_gerekli is not None else False)
                
                # Satın alma onay yetkisi
                try:
                    if hasattr(row, 'satinalma_onay_yetkisi'):
                        self.chk_satinalma_onay.setChecked(bool(row.satinalma_onay_yetkisi) if row.satinalma_onay_yetkisi is not None else False)
                except Exception:
                    pass

                # Kart ID
                try:
                    if hasattr(row, 'kart_id'):
                        self.txt_kart_id.setText(row.kart_id or '')
                except Exception:
                    pass

                # Terminal PIN durumu
                try:
                    if hasattr(row, 'terminal_pin_set') and row.terminal_pin_set:
                        son = ''
                        try:
                            if hasattr(row, 'terminal_pin_son_degisim') and row.terminal_pin_son_degisim:
                                son = f" (son: {row.terminal_pin_son_degisim.strftime('%Y-%m-%d')})"
                        except Exception:
                            pass
                        self.lbl_pin_durum.setText(f"PIN tanimli{son}")
                        self.lbl_pin_durum.setStyleSheet(f"color: {brand.SUCCESS}; font-weight: bold;")
                    else:
                        self.lbl_pin_durum.setText("PIN tanimli degil")
                        self.lbl_pin_durum.setStyleSheet(f"color: {brand.TEXT_DIM};")
                except Exception:
                    pass
                
                # Rol seçimi
                if row.rol_id:
                    for i in range(self.cmb_rol.count()):
                        if self.cmb_rol.itemData(i) == row.rol_id:
                            self.cmb_rol.setCurrentIndex(i)
                            break
                
                # Personel seçimi
                if row.personel_id:
                    for i in range(self.cmb_personel.count()):
                        if self.cmb_personel.itemData(i) == row.personel_id:
                            self.cmb_personel.setCurrentIndex(i)
                            break
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kullanıcı yüklenirken hata: {str(e)}")
    
    def kaydet(self):
        """Kullanıcıyı kaydet"""
        kullanici_adi = self.txt_kullanici_adi.text().strip()
        email = self.txt_email.text().strip()
        ad = self.txt_ad.text().strip()
        soyad = self.txt_soyad.text().strip()
        telefon = self.txt_telefon.text().strip()
        sifre = self.txt_sifre.text()
        sifre_tekrar = self.txt_sifre_tekrar.text()
        
        # Validasyon
        if not kullanici_adi:
            QMessageBox.warning(self, "Uyarı", "Kullanıcı adı zorunludur!")
            return
        
        if not email:
            QMessageBox.warning(self, "Uyarı", "E-posta zorunludur!")
            return
        
        # Yeni kullanıcı için şifre zorunlu
        if not self.kullanici_id and not sifre:
            QMessageBox.warning(self, "Uyarı", "Şifre zorunludur!")
            return
        
        if sifre and sifre != sifre_tekrar:
            QMessageBox.warning(self, "Uyarı", "Şifreler eşleşmiyor!")
            return
        
        if sifre and len(sifre) < 6:
            QMessageBox.warning(self, "Uyarı", "Şifre en az 6 karakter olmalıdır!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Kullanıcı adı ve email unique kontrolü
            if self.kullanici_id:
                cursor.execute("""
                    SELECT id FROM sistem.kullanicilar 
                    WHERE (kullanici_adi = ? OR email = ?) AND id != ? AND ISNULL(silindi_mi, 0) = 0
                """, [kullanici_adi, email, self.kullanici_id])
            else:
                cursor.execute("""
                    SELECT id FROM sistem.kullanicilar 
                    WHERE (kullanici_adi = ? OR email = ?) AND ISNULL(silindi_mi, 0) = 0
                """, [kullanici_adi, email])
            
            if cursor.fetchone():
                QMessageBox.warning(self, "Uyarı", "Bu kullanıcı adı veya e-posta zaten kullanılıyor!")
                conn.close()
                return

            # Kart ID benzersizlik kontrolü
            kart_id = self.txt_kart_id.text().strip() or None
            if kart_id:
                if self.kullanici_id:
                    cursor.execute("""
                        SELECT id FROM sistem.kullanicilar
                        WHERE kart_id = ? AND id != ? AND ISNULL(silindi_mi, 0) = 0
                    """, [kart_id, self.kullanici_id])
                else:
                    cursor.execute("""
                        SELECT id FROM sistem.kullanicilar
                        WHERE kart_id = ? AND ISNULL(silindi_mi, 0) = 0
                    """, [kart_id])

                if cursor.fetchone():
                    QMessageBox.warning(self, "Uyarı", "Bu kart ID zaten başka bir kullanıcıya atanmış!")
                    conn.close()
                    return

            rol_id = self.cmb_rol.currentData()
            personel_id = self.cmb_personel.currentData()
            aktif_mi = 1 if self.chk_aktif.isChecked() else 0
            kilitli_mi = 1 if self.chk_kilitli.isChecked() else 0
            sifre_degisim = 1 if self.chk_sifre_degistir.isChecked() else 0
            
            if self.kullanici_id:
                # Güncelleme
                if sifre:
                    # Şifre ile güncelle (bcrypt format için basit hash)
                    sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
                    satinalma_onay = 1 if self.chk_satinalma_onay.isChecked() else 0
                    cursor.execute("""
                        UPDATE sistem.kullanicilar SET
                            kullanici_adi = ?,
                            email = ?,
                            ad = ?,
                            soyad = ?,
                            telefon = ?,
                            sifre_hash = ?,
                            kart_id = ?,
                            rol_id = ?,
                            personel_id = ?,
                            aktif_mi = ?,
                            hesap_kilitli_mi = ?,
                            sifre_degisim_gerekli = ?,
                            satinalma_onay_yetkisi = ?,
                            guncelleme_tarihi = GETDATE()
                        WHERE id = ?
                    """, [kullanici_adi, email, ad, soyad, telefon, sifre_hash,
                          kart_id, rol_id, personel_id, aktif_mi, kilitli_mi, sifre_degisim,
                          satinalma_onay, self.kullanici_id])
                else:
                    # Şifresiz güncelle
                    satinalma_onay = 1 if self.chk_satinalma_onay.isChecked() else 0
                    cursor.execute("""
                        UPDATE sistem.kullanicilar SET
                            kullanici_adi = ?,
                            email = ?,
                            ad = ?,
                            soyad = ?,
                            telefon = ?,
                            kart_id = ?,
                            rol_id = ?,
                            personel_id = ?,
                            aktif_mi = ?,
                            hesap_kilitli_mi = ?,
                            sifre_degisim_gerekli = ?,
                            satinalma_onay_yetkisi = ?,
                            guncelleme_tarihi = GETDATE()
                        WHERE id = ?
                    """, [kullanici_adi, email, ad, soyad, telefon,
                          kart_id, rol_id, personel_id, aktif_mi, kilitli_mi, sifre_degisim,
                          satinalma_onay, self.kullanici_id])
            else:
                # Yeni kayıt
                import uuid
                new_uuid = str(uuid.uuid4())
                sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
                satinalma_onay = 1 if self.chk_satinalma_onay.isChecked() else 0
                
                cursor.execute("""
                    INSERT INTO sistem.kullanicilar
                    (uuid, kullanici_adi, email, ad, soyad, telefon, sifre_hash, kart_id,
                     rol_id, personel_id, aktif_mi, hesap_kilitli_mi,
                     sifre_degisim_gerekli, satinalma_onay_yetkisi, olusturma_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), 0)
                """, [new_uuid, kullanici_adi, email, ad, soyad, telefon, sifre_hash, kart_id,
                      rol_id, personel_id, aktif_mi, kilitli_mi, sifre_degisim, satinalma_onay])
            
            conn.commit()
            
            # Log kaydet
            if self.kullanici_id:
                LogManager.log_update('sistem', 'kullanicilar', self.kullanici_id,
                                     aciklama=f'Kullanıcı güncellendi: {kullanici_adi}')
            else:
                # Yeni eklenen ID'yi al
                cursor.execute("SELECT MAX(id) FROM sistem.kullanicilar WHERE kullanici_adi = ?", [kullanici_adi])
                yeni_id = cursor.fetchone()[0]
                LogManager.log_insert('sistem', 'kullanicilar', yeni_id,
                                     aciklama=f'Yeni kullanıcı eklendi: {kullanici_adi}')
            
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Kullanıcı kaydedildi!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")

    def _terminal_pin_ayarla(self):
        """4-6 haneli PIN al, hash'le ve sistem.kullanicilar tablosuna yaz."""
        if not self.kullanici_id:
            QMessageBox.information(self, "Once Kaydet",
                "PIN ayarlamak icin once kullaniciyi kaydedin, sonra tekrar acin.")
            return

        from PySide6.QtWidgets import QDialog as QD, QFormLayout as QF, QLineEdit as QL
        from PySide6.QtGui import QIntValidator

        dlg = QD(self)
        dlg.setWindowTitle("Terminal PIN Ayarla")
        dlg.setMinimumWidth(360)
        v = QVBoxLayout(dlg)
        info = QLabel(
            "El terminali (EDA51) veya tabletten giris icin 4 ya da 6 haneli sayisal PIN girin.\n"
            "Bu PIN sadece terminal/tablet erisimi icindir; web girisi icin SIFRE alani kullanilir."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {brand.TEXT_DIM}; padding-bottom: 8px;")
        v.addWidget(info)

        f = QF()
        ed_pin = QL()
        ed_pin.setEchoMode(QL.Password)
        ed_pin.setMaxLength(6)
        ed_pin.setValidator(QIntValidator(0, 999999))
        ed_pin.setPlaceholderText("4 veya 6 hane")
        f.addRow("Yeni PIN:", ed_pin)
        ed_pin2 = QL()
        ed_pin2.setEchoMode(QL.Password)
        ed_pin2.setMaxLength(6)
        ed_pin2.setValidator(QIntValidator(0, 999999))
        ed_pin2.setPlaceholderText("Tekrar")
        f.addRow("Tekrar:", ed_pin2)
        v.addLayout(f)

        btns = QHBoxLayout()
        btns.addStretch()
        b_iptal = QPushButton("Iptal")
        b_iptal.clicked.connect(dlg.reject)
        b_kaydet = QPushButton("Kaydet")
        b_kaydet.setStyleSheet(
            f"QPushButton {{ background:{brand.PRIMARY}; color:white; padding:6px 14px; "
            f"border:none; border-radius:6px; font-weight:bold; }}"
        )
        b_kaydet.clicked.connect(dlg.accept)
        btns.addWidget(b_iptal)
        btns.addWidget(b_kaydet)
        v.addLayout(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        pin = ed_pin.text().strip()
        pin2 = ed_pin2.text().strip()
        if pin != pin2:
            QMessageBox.warning(self, "Eslesmiyor", "Iki PIN alani ayni olmali.")
            return
        if len(pin) not in (4, 6) or not pin.isdigit():
            QMessageBox.warning(self, "Gecersiz", "PIN 4 veya 6 haneli sayisal deger olmali.")
            return

        # Hash mantigi: SHA-256 + per-kullanici salt (terminal_api/auth.py ile ayni!)
        import hashlib
        salt = f"nexor-terminal-pin-v1::{self.kullanici_id}::"
        pin_hash = hashlib.sha256((salt + pin).encode("utf-8")).hexdigest()

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE sistem.kullanicilar
                SET terminal_pin_hash = ?,
                    terminal_pin_set = 1,
                    terminal_pin_son_degisim = SYSDATETIME()
                WHERE id = ?
            """, [pin_hash, self.kullanici_id])
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "DB Hatasi", str(e))
            return

        self.lbl_pin_durum.setText(f"PIN tanimli (yeni)")
        self.lbl_pin_durum.setStyleSheet(f"color: {brand.SUCCESS}; font-weight: bold;")
        QMessageBox.information(self, "Tamam",
            f"Terminal PIN ayarlandi.\nKullanici '{self.txt_kullanici_adi.text()}' bu PIN ile el terminaline giris yapabilir.")

    def _terminal_pin_sil(self):
        if not self.kullanici_id:
            return
        if QMessageBox.question(self, "PIN Sil",
            "Bu kullanicinin terminal PIN'i silinsin mi?\nKart yoksa terminal'e giris yapamayacak."
        ) != QMessageBox.Yes:
            return
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE sistem.kullanicilar
                SET terminal_pin_hash = NULL,
                    terminal_pin_set = 0,
                    terminal_pin_son_degisim = SYSDATETIME()
                WHERE id = ?
            """, [self.kullanici_id])
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "DB Hatasi", str(e))
            return
        self.lbl_pin_durum.setText("PIN tanimli degil")
        self.lbl_pin_durum.setStyleSheet(f"color: {brand.TEXT_DIM};")

    def _toggle_kart_okuma(self, checked: bool):
        """Kart okuma modunu aç/kapa."""
        self._rfid_reading = checked
        self._rfid_reader.set_active(checked)
        if checked:
            self.btn_kart_okut.setText("Bekleniyor...")
            self.txt_kart_id.setPlaceholderText("Kart\u0131 okuyucuya okutun...")
            # Mevcut alan değerlerini kaydet (kart karakterleri kirletebilir)
            self._saved_field_texts = {}
            for widget in self.findChildren(QLineEdit):
                if widget is not self.txt_kart_id:
                    self._saved_field_texts[widget] = widget.text()
                    widget.installEventFilter(self)
        else:
            self.btn_kart_okut.setText("Kart Okut")
            self.txt_kart_id.setPlaceholderText("Kart okutarak atay\u0131n...")
            for widget in self.findChildren(QLineEdit):
                if widget is not self.txt_kart_id:
                    widget.removeEventFilter(self)

    def _on_card_read(self, card_id: str):
        """RFID okuyucudan kart ID al\u0131nd\u0131\u011f\u0131nda."""
        self.txt_kart_id.setText(card_id)
        # Kart karakterleri ile kirlenen alanları eski haline getir
        for widget, text in getattr(self, '_saved_field_texts', {}).items():
            widget.setText(text)
        self._saved_field_texts = {}
        # Okumayı kapat
        self.btn_kart_okut.setChecked(False)

    def eventFilter(self, watched, event):
        """Kart okuma aktifken tu\u015f vuru\u015flar\u0131n\u0131 RFID okuyucuya y\u00f6nlendir."""
        if self._rfid_reading and event.type() == QEvent.Type.KeyPress:
            if self._rfid_reader.process_key(event):
                return True
        return super().eventFilter(watched, event)


class SistemKullaniciPage(BasePage):
    """Sistem Kullanici Yonetimi Sayfasi - PRAXIS Kurumsal UI"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = self._get_style()
        self.kullanicilar = []
        self._setup_ui()
        QTimer.singleShot(100, self.load_data)

    def _get_style(self) -> dict:
        """PRAXIS kurumsal tema"""
        t = self.theme
        return {
            'card_bg': brand.BG_CARD,
            'input_bg': brand.BG_INPUT,
            'border': brand.BORDER,
            'text': brand.TEXT,
            'text_secondary': brand.TEXT_MUTED,
            'text_muted': brand.TEXT_MUTED,
            'primary': brand.PRIMARY,
            'success': brand.SUCCESS,
            'warning': brand.WARNING,
            'error': brand.ERROR,
            'info': brand.INFO,
        }

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── Header (Praxis: accent bar + baslik) ──
        header = QHBoxLayout()

        title_section = QVBoxLayout()
        title_section.setSpacing(4)

        title_row = QHBoxLayout()
        accent = QFrame()
        accent.setFixedSize(4, 36)
        accent.setStyleSheet(f"background: {s['primary']}; border-radius: 2px;")
        title_row.addWidget(accent)

        title = QLabel("Kullanici Yonetimi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 22px; font-weight: 600; margin-left: 12px;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)

        self.lbl_subtitle = QLabel("Kayitlar yukleniyor...")
        self.lbl_subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; margin-left: 16px;")
        title_section.addWidget(self.lbl_subtitle)

        header.addLayout(title_section)
        header.addStretch()

        # Sag: Arama + Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("Kullanici ara...")
        self.txt_arama.setFixedWidth(220)
        self.txt_arama.textChanged.connect(self.filter_data)
        self.txt_arama.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        btn_layout.addWidget(self.txt_arama)

        btn_yeni = QPushButton("+ Yeni Kullanici")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.clicked.connect(self.yeni_kullanici)
        btn_yeni.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: #D42A2A; }}
            QPushButton:pressed {{ background: #9B1818; }}
        """)
        btn_layout.addWidget(btn_yeni)

        btn_refresh = QPushButton("\u21bb")
        btn_refresh.setToolTip("Yenile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setFixedSize(40, 40)
        btn_refresh.clicked.connect(self.load_data)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        btn_layout.addWidget(btn_refresh)

        header.addLayout(btn_layout)
        layout.addLayout(header)

        # ── Tablo ──
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "KULLANICI ADI", "AD SOYAD", "E-POSTA", "ROL", "SON GIRIS", "DURUM", "ISLEMLER"
        ])

        # Sutun genislikleri - Islemler icin sabit alan
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(6, QHeaderView.Fixed)
        h.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 245)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self.duzenle_kullanici)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{
                background: rgba(196, 30, 30, 0.15);
                color: {s['text']};
            }}
            QTableWidget::item:hover {{
                background: rgba(196, 30, 30, 0.06);
            }}
            QHeaderView::section {{
                background: #111822;
                color: {s['text_secondary']};
                padding: 12px 10px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {s['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #2A3545;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        layout.addWidget(self.table, 1)

    def load_data(self):
        """Kullanicilari yukle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT k.id, k.kullanici_adi, k.ad, k.soyad, k.email,
                       k.son_giris_tarihi, k.aktif_mi, k.hesap_kilitli_mi,
                       ISNULL(r.rol_adi, r.ad) as rol_adi
                FROM sistem.kullanicilar k
                LEFT JOIN sistem.roller r ON k.rol_id = r.id
                WHERE ISNULL(k.silindi_mi, 0) = 0
                ORDER BY k.kullanici_adi
            """)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            self.kullanicilar = [dict(zip(columns, row)) for row in rows]
            self.lbl_subtitle.setText(f"Toplam {len(self.kullanicilar)} kullanici")
            self.display_data(self.kullanicilar)

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yuklenirken hata: {str(e)}")

    def display_data(self, data):
        """Verileri tabloda goster — Praxis stili"""
        s = self.s
        self.table.setRowCount(len(data))

        for row_idx, k in enumerate(data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(k.get('id', ''))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(k.get('kullanici_adi', '')))

            ad_soyad = f"{k.get('ad', '') or ''} {k.get('soyad', '') or ''}".strip()
            self.table.setItem(row_idx, 2, QTableWidgetItem(ad_soyad))

            self.table.setItem(row_idx, 3, QTableWidgetItem(k.get('email', '')))
            self.table.setItem(row_idx, 4, QTableWidgetItem(k.get('rol_adi', '') or '-'))

            son_giris = k.get('son_giris_tarihi')
            son_giris_str = son_giris.strftime('%Y-%m-%d %H:%M') if son_giris else '-'
            self.table.setItem(row_idx, 5, QTableWidgetItem(son_giris_str))

            # Durum — Praxis: renkli nokta + metin
            if k.get('hesap_kilitli_mi'):
                durum = "\u25cf Kilitli"
                durum_renk = s['error']
            elif k.get('aktif_mi'):
                durum = "\u25cf Aktif"
                durum_renk = s['success']
            else:
                durum = "\u25cf Pasif"
                durum_renk = s['warning']

            durum_item = QTableWidgetItem(durum)
            durum_item.setForeground(QColor(durum_renk))
            self.table.setItem(row_idx, 6, durum_item)

            # Islem butonlari
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, kid=k.get('id'): self.duzenle_by_id(kid), "edit"),
                ("\U0001f511", "Sifre Sifirla", lambda checked, kid=k.get('id'): self.sifre_sifirla(kid), "view"),
                ("🗑️", "Sil", lambda checked, kid=k.get('id'): self.sil_kullanici(kid), "delete"),
            ])
            self.table.setCellWidget(row_idx, 7, widget)
            self.table.setRowHeight(row_idx, 42)
    
    def filter_data(self):
        """Arama filtresi"""
        arama = self.txt_arama.text().lower()
        if not arama:
            self.display_data(self.kullanicilar)
            return
        
        filtered = [k for k in self.kullanicilar if 
                    arama in (k.get('kullanici_adi', '') or '').lower() or
                    arama in (k.get('ad', '') or '').lower() or
                    arama in (k.get('soyad', '') or '').lower() or
                    arama in (k.get('email', '') or '').lower()]
        self.display_data(filtered)
    
    def yeni_kullanici(self):
        """Yeni kullanıcı ekle"""
        dialog = KullaniciDialog(self, self.theme)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def duzenle_kullanici(self):
        """Seçili kullanıcıyı düzenle"""
        row = self.table.currentRow()
        if row >= 0:
            kullanici_id = int(self.table.item(row, 0).text())
            self.duzenle_by_id(kullanici_id)
    
    def duzenle_by_id(self, kullanici_id):
        """ID ile kullanıcı düzenle"""
        dialog = KullaniciDialog(self, self.theme, kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def sifre_sifirla(self, kullanici_id):
        """Şifre sıfırla"""
        reply = QMessageBox.question(
            self, "Şifre Sıfırla",
            "Kullanıcının şifresini sıfırlamak istediğinize emin misiniz?\n\n"
            "Yeni şifre: 123456",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                yeni_sifre_hash = hashlib.sha256("123456".encode()).hexdigest()
                cursor.execute("""
                    UPDATE sistem.kullanicilar 
                    SET sifre_hash = ?, sifre_degisim_gerekli = 1, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, [yeni_sifre_hash, kullanici_id])
                
                conn.commit()
                conn.close()
                
                # Log kaydet
                LogManager.log_update('sistem', 'kullanicilar', kullanici_id,
                                     aciklama=f'Kullanıcı şifresi sıfırlandı (ID: {kullanici_id})')
                
                QMessageBox.information(self, "Başarılı", "Şifre sıfırlandı!\nYeni şifre: 123456")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Şifre sıfırlama hatası: {str(e)}")
    
    def sil_kullanici(self, kullanici_id):
        """Kullanıcıyı soft delete"""
        reply = QMessageBox.question(
            self, "Kullanıcı Sil",
            "Bu kullanıcıyı silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Silinen kullanıcı adını al
                cursor.execute("SELECT kullanici_adi FROM sistem.kullanicilar WHERE id = ?", [kullanici_id])
                row = cursor.fetchone()
                kullanici_adi = row.kullanici_adi if row else str(kullanici_id)
                
                cursor.execute("""
                    UPDATE sistem.kullanicilar 
                    SET silindi_mi = 1, silinme_tarihi = GETDATE(), aktif_mi = 0
                    WHERE id = ?
                """, [kullanici_id])
                
                conn.commit()
                conn.close()
                
                # Log kaydet
                LogManager.log_delete('sistem', 'kullanicilar', kullanici_id,
                                     aciklama=f'Kullanıcı silindi: {kullanici_adi}')
                
                QMessageBox.information(self, "Başarılı", "Kullanıcı silindi!")
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
