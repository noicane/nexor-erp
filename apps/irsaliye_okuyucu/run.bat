@echo off
REM NEXOR Irsaliye Okuyucu - Windows baslatma scripti
REM Calistir: run.bat (ya da cift tikla)

cd /d "%~dp0"

REM Sanal ortam yoksa olustur
if not exist ".venv" (
    echo [Kurulum] Python sanal ortami olusturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo HATA: Python bulunamadi. Python 3.10+ kurulu olmali.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    echo [Kurulum] Paketler yukleniyor...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM .env yoksa uyar
if not exist ".env" (
    echo.
    echo ========================================
    echo UYARI: .env dosyasi yok!
    echo .env.example'i kopyala, icini doldur:
    echo    copy .env.example .env
    echo    notepad .env
    echo ========================================
    echo.
    pause
)

REM Sunucuyu baslat
echo.
echo ========================================
echo NEXOR Irsaliye Okuyucu baslatiliyor...
echo.
echo Yerel:     http://localhost:8000
echo LAN (bu PC):  http://192.168.10.66:8000
echo ========================================
echo.

python server.py
pause
