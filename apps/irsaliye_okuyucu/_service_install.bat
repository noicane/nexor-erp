@echo off
REM NEXOR OCR - Windows Service kurulumu (NSSM)
setlocal
set LOG=C:\Nexor\irsaliye_okuyucu\_service_install.log
echo [%DATE% %TIME%] Service install basladi > %LOG%

set NSSM=C:\nssm\nssm.exe
set PYTHON=C:\Nexor\irsaliye_okuyucu\.venv\Scripts\python.exe
set SERVER=C:\Nexor\irsaliye_okuyucu\server.py
set APPDIR=C:\Nexor\irsaliye_okuyucu
set SVC=NexorOCR

REM NSSM bul
if not exist "%NSSM%" (
    echo HATA: NSSM bulunamadi: %NSSM% >> %LOG%
    exit /b 1
)

REM Eski servis varsa kaldir
"%NSSM%" stop %SVC% >> %LOG% 2>&1
"%NSSM%" remove %SVC% confirm >> %LOG% 2>&1

REM Yeni servis
echo [%TIME%] Service olusturuluyor... >> %LOG%
"%NSSM%" install %SVC% "%PYTHON%" "%SERVER%" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppDirectory "%APPDIR%" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppStdout "%APPDIR%\service_stdout.log" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppStderr "%APPDIR%\service_stderr.log" >> %LOG% 2>&1
"%NSSM%" set %SVC% AppRotateFiles 1 >> %LOG% 2>&1
"%NSSM%" set %SVC% AppRotateBytes 10485760 >> %LOG% 2>&1
"%NSSM%" set %SVC% AppRestartDelay 5000 >> %LOG% 2>&1
"%NSSM%" set %SVC% Description "NEXOR Irsaliye OCR - Tabletten mal giris" >> %LOG% 2>&1
"%NSSM%" set %SVC% Start SERVICE_AUTO_START >> %LOG% 2>&1

REM Firewall port 8001
echo [%TIME%] Firewall kurali... >> %LOG%
netsh advfirewall firewall delete rule name="NEXOR_OCR_8001" >nul 2>&1
netsh advfirewall firewall add rule name="NEXOR_OCR_8001" dir=in action=allow protocol=TCP localport=8001 >> %LOG% 2>&1

REM Servisi baslat
echo [%TIME%] Servis baslatiliyor... >> %LOG%
"%NSSM%" start %SVC% >> %LOG% 2>&1

REM Durum
timeout /t 5 /nobreak > nul
sc query %SVC% >> %LOG% 2>&1

echo [%TIME%] Tamam >> %LOG%
endlocal
exit /b 0
