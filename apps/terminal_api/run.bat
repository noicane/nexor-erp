@echo off
REM NEXOR Terminal API - Yerel calisma
REM Asagidaki komut NEXOR root'undan calistirilir.

cd /d %~dp0..\..

if not exist venv\Scripts\activate.bat (
    echo HATA: NEXOR root'unda venv yok. Once: python -m venv venv ^&^& venv\Scripts\pip install -r apps\terminal_api\requirements.txt
    exit /b 1
)

call venv\Scripts\activate.bat

echo NEXOR Terminal API baslatiliyor (port 8002)...
echo.
python -m uvicorn apps.terminal_api.main:app --host 0.0.0.0 --port 8002 --reload
