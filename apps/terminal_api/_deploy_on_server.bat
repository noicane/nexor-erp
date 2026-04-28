@echo off
REM NEXOR Terminal API - Server deploy (C:\Nexor\terminal_api altinda calisir)
REM Server'da schtasks ile tetiklenir. Venv olusturur, paketleri yukler.
setlocal
set LOG=C:\Nexor\terminal_api\_deploy.log
echo [%DATE% %TIME%] Deploy basladi > %LOG%

set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe
set APPDIR=C:\Nexor\terminal_api

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
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt python-dotenv >> %LOG% 2>&1
if errorlevel 1 (
    echo HATA: pip install basarisiz >> %LOG%
    exit /b 1
)

REM 3) Paket dogrulama
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, jwt, pyodbc, passlib, dotenv; print('Paketler OK')" >> %LOG% 2>&1
if errorlevel 1 (
    echo HATA: paket import basarisiz >> %LOG%
    exit /b 1
)

echo [%TIME%] Deploy tamam. Service install icin _service_install.bat calistirin. >> %LOG%
endlocal
exit /b 0
