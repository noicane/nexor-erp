# Server Kurulumu (192.168.10.66)

Bu dosya `C:\Nexor\irsaliye_okuyucu\` klasorune kopyalandi. Kurulumu tamamlamak icin:

## 1) Python kur (yoksa) — 3 dakika

- https://www.python.org/downloads/windows/ → **Python 3.12.x** indir
- Kurulumda:
  - ☑ **"Add Python to PATH"** isaretle (zorunlu!)
  - "Install for all users" sec
- Kurulum sonrasi CMD'yi kapat/ac, test: `python --version`

## 2) .env dosyasi olustur

```cmd
cd C:\Nexor\irsaliye_okuyucu
copy .env.example .env
notepad .env
```

`.env` icinde:
```
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXX
```
satirina **Anthropic API key'i** yapistir, kaydet.

## 3) Ilk calistirma (kurulum) — 2 dakika

```cmd
cd C:\Nexor\irsaliye_okuyucu
run.bat
```
- Otomatik olarak `.venv` olusturur, paketleri yukler, sunucuyu baslatir
- http://localhost:8000 acik olmali
- CTRL+C ile kapat

## 4) Firewall portunu ac

Admin CMD'de:
```cmd
netsh advfirewall firewall add rule name="NEXOR_OCR_8000" dir=in action=allow protocol=TCP localport=8000
```

## 5) NSSM ile Windows Service yap (otomatik baslasin)

```cmd
REM nssm server'da C:\nssm\ altinda kurulu
C:\nssm\nssm.exe install NexorOCR "C:\Nexor\irsaliye_okuyucu\.venv\Scripts\python.exe" "C:\Nexor\irsaliye_okuyucu\server.py"

REM Calisma dizini
C:\nssm\nssm.exe set NexorOCR AppDirectory "C:\Nexor\irsaliye_okuyucu"

REM Log dosyalari
C:\nssm\nssm.exe set NexorOCR AppStdout "C:\Nexor\irsaliye_okuyucu\service_stdout.log"
C:\nssm\nssm.exe set NexorOCR AppStderr "C:\Nexor\irsaliye_okuyucu\service_stderr.log"

REM Aciklama
C:\nssm\nssm.exe set NexorOCR Description "NEXOR Irsaliye OCR - Tabletten mal giris"

REM Otomatik baslat
C:\nssm\nssm.exe set NexorOCR Start SERVICE_AUTO_START

REM Servisi baslat
C:\nssm\nssm.exe start NexorOCR
```

Durum kontrolu:
```cmd
sc query NexorOCR
```

## Erisim

- Server icinden: http://localhost:8000
- Tablet/telefon (LAN): **http://192.168.10.66:8000**

## Sorun giderme

| Sorun | Cozum |
|---|---|
| `python` komutu bulunamadi | PATH eklendi mi? CMD'yi kapat/ac |
| `run.bat` hata verir | Admin CMD'de deneyin |
| Tablet baglanmiyor | Firewall kurali ekledi mi? (adim 4) |
| Servis calismiyor | `type service_stderr.log` ile hataya bak |

## Servisi yeniden baslat

```cmd
net stop NexorOCR
net start NexorOCR
```

## Servisi kaldir

```cmd
C:\nssm\nssm.exe remove NexorOCR confirm
```
