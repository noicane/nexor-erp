@echo off
REM NEXOR Terminal API - Windows Service kurulumu (NSSM)
setlocal
set LOG=C:\Nexor\terminal_api\_service_install.log
echo [%DATE% %TIME%] Service install basladi > %LOG%

set NSSM=C:\nssm\nssm.exe
set PYTHON=C:\Nexor\terminal_api\.venv\Scripts\python.exe
set APPDIR=C:\Nexor\terminal_api
set SVC=NexorTerminal
set PORT=8002

if not exist "%NSSM%" (
    echo HATA: NSSM bulunamadi: %NSSM% >> %LOG%
    exit /b 1
)

REM Eski servis varsa kaldir
"%NSSM%" stop %SVC% >> %LOG% 2>&1
"%NSSM%" remove %SVC% confirm >> %LOG% 2>&1

REM Yeni servis - uvicorn module olarak (apps.terminal_api.main:app)
REM AppDirectory C:\Nexor olmali ki "apps.terminal_api" import calissin
echo [%TIME%] Service olusturuluyor... >> %LOG%
"%NSSM%" install %SVC% "%PYTHON%" "-m uvicorn terminal_api.main:app --host 0.0.0.0 --port %PORT%" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppDirectory "C:\Nexor" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppStdout "%APPDIR%\service_stdout.log" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppStderr "%APPDIR%\service_stderr.log" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppRotateFiles 1 >> %LOG% 2>&1
"%NSSM%" set %SVC% AppRotateBytes 10485760 >> %LOG% 2>&1
"%NSSM%" set %SVC% AppRestartDelay 5000 >> %LOG% 2>&1
"%NSSM%" set %SVC% Description "NEXOR Terminal API - Honeywell EDA51 sevkiyat el terminali" >> %LOG% 2>&1
"%NSSM%" set %SVC% Start SERVICE_AUTO_START >> %LOG% 2>&1

REM Firewall port 8002
echo [%TIME%] Firewall kurali... >> %LOG%
netsh advfirewall firewall delete rule name="NEXOR_TERMINAL_8002" >nul 2>&1
netsh advfirewall firewall add rule name="NEXOR_TERMINAL_8002" dir=in action=allow protocol=TCP localport=8002 >> %LOG% 2>&1

REM Servisi baslat
echo [%TIME%] Servis baslatiliyor... >> %LOG%
"%NSSM%" start %SVC% >> %LOG% 2>&1

REM Durum
timeout /t 5 /nobreak > nul
sc query %SVC% >> %LOG% 2>&1

echo [%TIME%] Tamam >> %LOG%
endlocal
exit /b 0
