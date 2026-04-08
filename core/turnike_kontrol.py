# -*- coding: utf-8 -*-
"""
NEXOR ERP - Turnike Uzaktan Kontrol (SSH üzerinden Orange Pi)

Fonksiyonlar:
  - Turnike servisini başlat/durdur
  - Turnikeyi manuel aç (giriş/çıkış)
  - Servis durumu sorgula
"""
import threading
import paramiko
import logging

logger = logging.getLogger("turnike_kontrol")

# Orange Pi bağlantı bilgileri
TURNIKE_HOST = "192.168.10.75"
TURNIKE_USER = "root"
TURNIKE_PASS = "1234"
TURNIKE_PORT = 22
SSH_TIMEOUT = 5

SERVICE_NAME = "pkds"


def _ssh_exec(command: str, timeout: int = SSH_TIMEOUT) -> tuple[bool, str]:
    """SSH üzerinden komut çalıştır. (success, output) döner."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(TURNIKE_HOST, port=TURNIKE_PORT,
                    username=TURNIKE_USER, password=TURNIKE_PASS,
                    timeout=timeout)
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        ssh.close()
        return True, out or err
    except Exception as e:
        logger.error("SSH hata: %s", e)
        return False, str(e)


def servis_durum() -> dict:
    """Turnike servis durumunu sorgula."""
    ok, out = _ssh_exec(f"systemctl is-active {SERVICE_NAME} 2>/dev/null && echo RUNNING || echo STOPPED")
    running = "RUNNING" in out if ok else False

    # Son log satırları
    _, log_out = _ssh_exec(f"tail -5 /home/pkds/PKDS/pkds_turnike.log 2>/dev/null")

    return {
        "online": ok,
        "running": running,
        "detail": out if ok else f"Bağlantı hatası: {out}",
        "log": log_out
    }


def servis_baslat() -> tuple[bool, str]:
    """Turnike servisini başlat."""
    ok, out = _ssh_exec(f"systemctl start {SERVICE_NAME} && echo OK")
    return ok and "OK" in out, out


def servis_durdur() -> tuple[bool, str]:
    """Turnike servisini durdur."""
    ok, out = _ssh_exec(f"systemctl stop {SERVICE_NAME} && echo OK")
    return ok and "OK" in out, out


def servis_yeniden_baslat() -> tuple[bool, str]:
    """Turnike servisini yeniden başlat."""
    ok, out = _ssh_exec(f"systemctl restart {SERVICE_NAME} && echo OK")
    return ok and "OK" in out, out


def turnike_ac(yon: str = "giris") -> tuple[bool, str]:
    """
    Turnikeyi manuel aç - kontrol dosyası ile servis tetikleme.
    yon: 'giris' veya 'cikis'
    """
    if yon not in ("giris", "cikis"):
        return False, "Geçersiz yön"

    # Kontrol dosyası bırak - servis bunu okuyup turnikeyi açacak
    cmd = f"echo '{yon}' > /tmp/turnike_ac && echo OK"
    ok, out = _ssh_exec(cmd, timeout=5)
    if not ok or "OK" not in out:
        return False, f"Sinyal gönderilemedi: {out}"

    # 3 saniye bekleyip sonucu kontrol et
    import time
    time.sleep(3)
    ok2, out2 = _ssh_exec("cat /tmp/turnike_ac_sonuc 2>/dev/null && rm -f /tmp/turnike_ac_sonuc")
    if ok2 and "ACILDI" in out2:
        return True, f"Turnike açıldı ({yon})"

    # Fallback: Servisin kendi TurnikeKontrol'ünü kullan
    # Servisi durdur -> GPIO tetikle -> Servisi başlat
    pin = 5 if yon == "giris" else 8
    cmd_fallback = f"""systemctl stop pkds 2>/dev/null; sleep 0.3; python3 -c "
import OPi.GPIO as GPIO; import time
GPIO.setboard(GPIO.PRIME); GPIO.setwarnings(False); GPIO.setmode(GPIO.BOARD)
GPIO.setup({pin}, GPIO.OUT); GPIO.output({pin}, GPIO.LOW)
time.sleep(1.5); GPIO.output({pin}, GPIO.HIGH); GPIO.cleanup()
print('OK')
" 2>&1; systemctl start pkds"""
    ok3, out3 = _ssh_exec(cmd_fallback, timeout=15)
    success = ok3 and "OK" in out3
    return success, f"Turnike açıldı ({yon})" if success else out3


def ping_test() -> bool:
    """Cihaz erişilebilir mi?"""
    ok, _ = _ssh_exec("echo PONG", timeout=3)
    return ok
