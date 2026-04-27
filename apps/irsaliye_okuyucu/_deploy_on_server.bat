@echo off
REM NEXOR OCR - Server deploy (C:\Nexor\irsaliye_okuyucu altinda calisir)
REM Bu bat server'da schtasks ile tetiklenir
setlocal
set LOG=C:\Nexor\irsaliye_okuyucu\_deploy.log
echo [%DATE% %TIME%] Deploy basladi > %LOG%

set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe
set APPDIR=C:\Nexor\irsaliye_okuyucu

if not exist "%PYTHON%" (
    echo HATA: Python bulunamadi: %PYTHON% >> %LOG%
    exit /b 1
)

cd /d %APPDIR%

REM 1) Venv olustur
if not exist ".venv\Scripts\python.exe" (
    echo [%TIME%] Venv olusturuluyor... >> %LOG%
    "%PYTHON%" -m venv .venv >> %LOG% 2>&1
    if errorlevel 1 (
        echo HATA: venv olusturulamadi >> %LOG%
        exit /b 1
    )
)

REM 2) Paketleri yukle
echo [%TIME%] Paketler yukleniyor... >> %LOG%
".venv\Scripts\python.exe" -m pip install --upgrade pip -q >> %LOG% 2>&1
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt >> %LOG% 2>&1
if errorlevel 1 (
    echo HATA: pip install basarisiz >> %LOG%
    exit /b 1
)

REM 3) Port'u .env'de 8001 yap (NexorBackend 8000'de)
if not exist ".env" (
    echo [%TIME%] .env eksik - API key gerekli! >> %LOG%
) else (
    REM PORT satirini 8001'e guncelle (yoksa ekle)
    findstr /v /b "PORT=" .env > .env.tmp
    echo PORT=8001 >> .env.tmp
    move /y .env.tmp .env > nul
)

echo [%TIME%] Deploy tamam >> %LOG%

REM 4) Sunucu port test (onceden calisiyor mu?)
".venv\Scripts\python.exe" -c "import fastapi, anthropic, rapidfuzz, pyodbc; print('Paketler OK')" >> %LOG% 2>&1

echo [%TIME%] Son. .env API key + NSSM servis kurulumu gerekli. >> %LOG%
endlocal
exit /b 0
