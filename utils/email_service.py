# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - E-Mail Gonderim Servisi
SMTP ile e-mail gonderimi
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.database import get_db_connection


class EmailService:
    """E-Mail gonderim servisi"""

    def __init__(self):
        self.ayarlar = self._load_ayarlar()

    def _load_ayarlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sistem.email_ayarlari WHERE aktif_mi = 1")
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            return {
                'smtp_server': row[1],
                'smtp_port': row[2],
                'smtp_ssl': row[3],
                'gonderen_email': row[4],
                'gonderen_sifre': row[5],
                'gonderen_adi': row[6] or 'NEXOR ERP',
                'test_modu': row[8],
                'test_email': row[9],
            }
        except Exception as e:
            print(f"[EmailService] Ayarlar yuklenemedi: {e}")
            return None

    def gonder(self, alici_email: str, konu: str, icerik_html: str):
        """
        E-mail gonder

        Args:
            alici_email: Alici e-mail adresi
            konu: E-mail konusu
            icerik_html: HTML formatinda icerik

        Returns:
            (success: bool, message: str)
        """
        if not self.ayarlar:
            return False, "E-mail ayarlari yapilandirilmamis"

        if self.ayarlar['test_modu']:
            alici_email = self.ayarlar['test_email']
            konu = f"[TEST] {konu}"

        if not alici_email or '@' not in alici_email:
            return False, f"Gecersiz e-mail: {alici_email}"

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.ayarlar['gonderen_adi']} <{self.ayarlar['gonderen_email']}>"
            msg['To'] = alici_email
            msg['Subject'] = konu

            msg.attach(MIMEText(icerik_html, 'html', 'utf-8'))

            if self.ayarlar['smtp_ssl'] and self.ayarlar['smtp_port'] == 465:
                server = smtplib.SMTP_SSL(self.ayarlar['smtp_server'], self.ayarlar['smtp_port'], timeout=15)
            else:
                server = smtplib.SMTP(self.ayarlar['smtp_server'], self.ayarlar['smtp_port'], timeout=15)
                if self.ayarlar['smtp_ssl']:
                    server.starttls()

            if self.ayarlar['gonderen_sifre']:
                server.login(self.ayarlar['gonderen_email'], self.ayarlar['gonderen_sifre'])

            server.send_message(msg)
            server.quit()

            print(f"[EmailService] Gonderildi: {alici_email}")
            return True, "Gonderildi"

        except Exception as e:
            print(f"[EmailService] Gonderim hatasi: {e}")
            return False, str(e)

    def toplu_gonder(self, alicilar: list, konu: str, icerik_html: str):
        """
        Toplu e-mail gonder

        Args:
            alicilar: [(kullanici_id, email), ...] listesi
        Returns:
            (basarili, toplam, hatalar)
        """
        basarili = 0
        hatalar = []
        for kid, email in alicilar:
            if not email or '@' not in str(email):
                continue
            ok, msg = self.gonder(email, konu, icerik_html)
            if ok:
                basarili += 1
            else:
                hatalar.append(f"{email}: {msg}")
        return basarili, len(alicilar), hatalar


_email_service = None


def get_email_service():
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def gonder_email(alici: str, konu: str, icerik_html: str):
    """Kolay kullanim wrapper"""
    service = get_email_service()
    return service.gonder(alici, konu, icerik_html)
