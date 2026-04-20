@echo off
setlocal EnableExtensions
title Nexor ERP - Kurulum

rem ============================================================
rem  NEXOR ERP - Otomatik Launcher Kurulum (per-user, no admin)
rem  Sunucudan NexorLauncher.exe kopyalar, kisayol olusturur,
rem  launcher'i baslatir.
rem ============================================================

set "SERVER_HOST=AtlasNas"
set "SERVER=\\%SERVER_HOST%\Atmo_Logic"
set "SRC=%SERVER%\launcher\NexorLauncher.exe"
set "DEST_DIR=%LOCALAPPDATA%\Nexor"
set "DEST=%DEST_DIR%\NexorLauncher.exe"
set "PSTMP=%TEMP%\NexorKur_%RANDOM%.ps1"

echo.
echo ============================================================
echo   NEXOR ERP - Kurulum Basladi
echo ============================================================
echo.
echo   Sunucu : %SERVER%
echo   Hedef  : %DEST_DIR%
echo.

rem --- 1a) Ag baglantisi (ping) ---
echo [*] Ag kontrolu: %SERVER_HOST% ...
ping -n 1 -w 1500 %SERVER_HOST% >nul 2>&1
if errorlevel 1 (
    echo [HATA] Sunucuya ping atilamiyor: %SERVER_HOST%
    echo        Ag/VPN baglantinizi kontrol edin.
    echo.
    pause
    exit /b 1
)
echo       Ping OK.

rem --- 1b) SMB paylasim erisimi (gerekirse credential prompt) ---
echo [*] Paylasim kontrolu: %SERVER% ...
dir "%SERVER%\launcher" >nul 2>&1
if errorlevel 1 (
    echo       Otomatik erisim yok, kimlik dogrulamasi gerekiyor.
    echo.
    echo   ============================================================
    echo   Lutfen sunucu kullanici adi ve sifrenizi girin.
    echo   Kullanici ornegi:  ATMOLOGIC\kullaniciadi  veya  kullaniciadi
    echo   ============================================================
    net use "%SERVER%" /persistent:no
    if errorlevel 1 (
        echo [HATA] Paylasima baglanilamadi: %SERVER%
        echo        Kullanici adi/sifre yanlis olabilir veya yetkiniz yok.
        echo.
        pause
        exit /b 1
    )
    dir "%SERVER%\launcher" >nul 2>&1
    if errorlevel 1 (
        echo [HATA] Baglanti kuruldu ama "launcher" klasoru gorunmuyor.
        pause
        exit /b 1
    )
)
echo       Paylasim OK.

if not exist "%SRC%" (
    echo [HATA] NexorLauncher.exe sunucuda bulunamadi:
    echo        %SRC%
    echo.
    pause
    exit /b 1
)

rem --- 2) Hedef klasor ---
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%" 2>nul

rem --- 3) Kopyala ---
echo [1/3] Launcher kopyalaniyor...
copy /Y "%SRC%" "%DEST%" >nul
if errorlevel 1 (
    echo [HATA] Kopyalama basarisiz: %DEST%
    echo        Launcher zaten calisiyorsa kapatip tekrar deneyin.
    pause
    exit /b 2
)
echo       Tamam: %DEST%

rem --- 4) Kisayollar (PowerShell, temp .ps1 ile - caret continuation guvensiz) ---
echo [2/3] Kisayollar olusturuluyor...
set "SC_DESK=%USERPROFILE%\Desktop\Nexor ERP.lnk"
set "SC_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Nexor ERP.lnk"

> "%PSTMP%" echo $ErrorActionPreference = 'Stop'
>>"%PSTMP%" echo try {
>>"%PSTMP%" echo   $ws = New-Object -ComObject WScript.Shell
>>"%PSTMP%" echo   foreach ($p in @('%SC_DESK%','%SC_MENU%')) {
>>"%PSTMP%" echo     $s = $ws.CreateShortcut($p)
>>"%PSTMP%" echo     $s.TargetPath       = '%DEST%'
>>"%PSTMP%" echo     $s.WorkingDirectory = '%DEST_DIR%'
>>"%PSTMP%" echo     $s.IconLocation     = '%DEST%,0'
>>"%PSTMP%" echo     $s.Description      = 'Nexor ERP'
>>"%PSTMP%" echo     $s.Save()
>>"%PSTMP%" echo   }
>>"%PSTMP%" echo   exit 0
>>"%PSTMP%" echo } catch {
>>"%PSTMP%" echo   Write-Host $_.Exception.Message
>>"%PSTMP%" echo   exit 1
>>"%PSTMP%" echo }

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PSTMP%"
set "PSRC=%ERRORLEVEL%"
del /Q "%PSTMP%" 2>nul

if not "%PSRC%"=="0" (
    echo [UYARI] Kisayol olusturulamadi (kod %PSRC%) - kurulum devam ediyor.
) else (
    echo       Masaustu : Nexor ERP.lnk
    echo       Baslat   : Nexor ERP.lnk
)

rem --- 5) Eski kisayollari temizle ---
if exist "%USERPROFILE%\Desktop\NexorERP.lnk" del /Q "%USERPROFILE%\Desktop\NexorERP.lnk" 2>nul
if exist "%USERPROFILE%\Desktop\Nexor.lnk"    del /Q "%USERPROFILE%\Desktop\Nexor.lnk"    2>nul

rem --- 5b) Launcher icin sunucu yolu override (registry) ---
rem Launcher hardcoded IP yerine bu yolu kullanir. Boylece AtlasNas hostname
rem cozulmeyen PC'lerde IP'ye geri donulmek istenirse buradan degistirilir.
set "SERVER_RELEASES=%SERVER%\releases"
reg add "HKCU\Software\Nexor" /v ServerPath /t REG_SZ /d "%SERVER_RELEASES%" /f >nul 2>&1
if errorlevel 1 (
    echo [UYARI] Registry'ye sunucu yolu yazilamadi (launcher default'u kullanir).
) else (
    echo       Sunucu yolu kaydedildi: %SERVER_RELEASES%
)

rem --- 6) Launcher'i baslat ---
echo [3/3] Nexor ERP baslatiliyor...
start "" "%DEST%"

echo.
echo ============================================================
echo   KURULUM TAMAMLANDI
echo ============================================================
echo.
echo   Bundan sonra masaustundeki "Nexor ERP" kisayolunu
echo   kullanabilirsiniz. Guncellemeler otomatik gelir.
echo.
timeout /t 4 >nul
exit /b 0
