@echo off
REM ====================================
REM NEXOR - Main.py CMD Başlatıcı  
REM Hataları görmek için
REM ====================================

echo.
echo ========================================
echo NEXOR ERP (Python) baslatiliyor...
echo ========================================
echo.
echo Hata mesajlari bu pencerede gorunecek.
echo Programi kapatmak icin bu pencereyi KAPATMAYIN!
echo.

REM NEXOR klasörüne git
cd /d "%~dp0"

REM main.py'yi çalıştır
python main.py

echo.
echo ========================================
echo Program kapandi!
echo Exit Code: %errorlevel%
echo ========================================
echo.

if %errorlevel% neq 0 (
    echo.
    echo !!! PROGRAM HATA ILE KAPANDI !!!
    echo Yukaridaki KIRMIZI mesajlari okuyun.
    echo.
)

echo.
echo Hatanin EKRAN GORUNTUSUNU alin (Win + Shift + S)
echo veya mesaji MOUSE ile secip kopyalayin.
echo.
echo Bu pencereyi kapatmak icin bir tusa basin...
pause >nul
