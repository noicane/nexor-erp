# -*- coding: utf-8 -*-
r"""
REDLINE NEXOR ERP - Self-Update Modülü v2
======================================
Versiyonlu deploy sistemine uygun otomatik güncelleme.

Yeni Yapı:
    \\AtlasNAS\Atmo_Logic\
    ├── versions\
    │   ├── 1.0.0\
    │   ├── 1.0.1\
    │   └── 1.0.2\
    ├── latest.txt          (en son versiyon numarası)
    └── installer\
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QFrame,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont


class UpdateInfo:
    """Güncelleme bilgisi container"""
    def __init__(self, data: dict, version: str = None):
        self.version = version or data.get('version', '0.0.0')
        self.build_date = data.get('build_date', '')
        self.force = data.get('force', False)
        self.min_version = data.get('min_version', '0.0.0')
        self.changelog = data.get('changelog', '')
        self.files = data.get('files', [])


class DownloadThread(QThread):
    """Dosya indirme thread'i - Versiyonlu yapı için"""
    progress = Signal(int, str)  # yüzde, durum mesajı
    finished = Signal(bool, str)  # başarılı mı, mesaj/hata
    
    def __init__(self, source_path: str, dest_path: str):
        super().__init__()
        self.source_path = Path(source_path)
        self.dest_path = Path(dest_path)
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        try:
            # Kaynak kontrolü
            if not self.source_path.exists():
                self.finished.emit(False, f"Kaynak bulunamadı: {self.source_path}")
                return
            
            # Toplam boyut hesapla
            total_size = self._get_total_size(self.source_path)
            copied_size = 0
            
            if total_size == 0:
                self.finished.emit(False, "Sunucuda dosya bulunamadı!")
                return
            
            # Hedef klasörü temizle
            if self.dest_path.exists():
                shutil.rmtree(self.dest_path)
            self.dest_path.mkdir(parents=True, exist_ok=True)
            
            # Dosyaları kopyala
            for item in self.source_path.iterdir():
                if self._cancelled:
                    self.finished.emit(False, "İndirme iptal edildi")
                    return
                
                if item.is_file():
                    copied_size = self._copy_file(item, self.dest_path / item.name, 
                                                   copied_size, total_size)
                elif item.is_dir():
                    copied_size = self._copy_dir(item, self.dest_path / item.name,
                                                  copied_size, total_size)
            
            self.progress.emit(100, "Tamamlandı!")
            self.finished.emit(True, str(self.dest_path))
            
        except PermissionError as e:
            self.finished.emit(False, f"Erişim hatası: {e}")
        except Exception as e:
            self.finished.emit(False, f"İndirme hatası: {e}")
    
    def _get_total_size(self, path: Path) -> int:
        """Toplam boyutu hesapla"""
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total
    
    def _copy_file(self, src: Path, dst: Path, copied: int, total: int) -> int:
        """Tek dosya kopyala"""
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        size = src.stat().st_size
        shutil.copy2(src, dst)
        copied += size
        
        percent = int((copied / total) * 100) if total > 0 else 0
        size_mb = copied / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        self.progress.emit(percent, f"İndiriliyor: {size_mb:.1f} MB / {total_mb:.1f} MB")
        
        return copied
    
    def _copy_dir(self, src: Path, dst: Path, copied: int, total: int) -> int:
        """Klasör kopyala (recursive)"""
        dst.mkdir(parents=True, exist_ok=True)
        
        for item in src.iterdir():
            if self._cancelled:
                return copied
            
            if item.is_file():
                copied = self._copy_file(item, dst / item.name, copied, total)
            elif item.is_dir():
                copied = self._copy_dir(item, dst / item.name, copied, total)
        
        return copied


class UpdateDialog(QDialog):
    """Güncelleme dialog'u - Progress bar ve changelog gösterimi"""
    
    def __init__(self, update_info: UpdateInfo, current_version: str, 
                 version_source_path: str, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self.version_source_path = version_source_path  # versions/x.x.x klasörü
        self.download_thread = None
        self.temp_dir = None
        
        self.setWindowTitle("Güncelleme Mevcut")
        self.setFixedSize(500, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Zorunlu güncelleme ise kapatma butonu gizle
        if self.update_info.force:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title = QLabel("🔄 Güncelleme Mevcut!")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Versiyon bilgisi
        version_frame = QFrame()
        version_frame.setStyleSheet("""
            QFrame {
                background: #2d3748;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        v_layout = QVBoxLayout(version_frame)
        
        current_lbl = QLabel(f"Mevcut versiyon: v{self.current_version}")
        current_lbl.setStyleSheet("color: #a0aec0;")
        v_layout.addWidget(current_lbl)
        
        new_lbl = QLabel(f"Yeni versiyon: v{self.update_info.version}")
        new_lbl.setStyleSheet("color: #48bb78; font-weight: bold; font-size: 14px;")
        v_layout.addWidget(new_lbl)
        
        if self.update_info.force:
            force_lbl = QLabel("⚠️ Bu güncelleme zorunludur!")
            force_lbl.setStyleSheet("color: #f6ad55; font-weight: bold;")
            v_layout.addWidget(force_lbl)
        
        layout.addWidget(version_frame)
        
        # Changelog
        if self.update_info.changelog:
            changelog_lbl = QLabel("📋 Neler Yeni?")
            changelog_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            layout.addWidget(changelog_lbl)
            
            changelog_text = QTextEdit()
            changelog_text.setPlainText(self.update_info.changelog)
            changelog_text.setReadOnly(True)
            changelog_text.setMaximumHeight(120)
            changelog_text.setStyleSheet("""
                QTextEdit {
                    background: #1a202c;
                    border: 1px solid #4a5568;
                    border-radius: 6px;
                    padding: 8px;
                    color: #e2e8f0;
                }
            """)
            layout.addWidget(changelog_text)
        
        # Progress bar (başlangıçta gizli)
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        p_layout = QVBoxLayout(self.progress_frame)
        p_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background: #2d3748;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4299e1, stop:1 #48bb78);
                border-radius: 6px;
            }
        """)
        p_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Hazırlanıyor...")
        self.progress_label.setStyleSheet("color: #a0aec0;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        p_layout.addWidget(self.progress_label)
        
        layout.addWidget(self.progress_frame)
        
        # Butonlar
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Sonra buton (zorunlu güncelleme değilse)
        self.later_btn = QPushButton("Sonra")
        self.later_btn.setFixedWidth(100)
        self.later_btn.setStyleSheet("""
            QPushButton {
                background: #4a5568;
                color: #e2e8f0;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5a6578;
            }
        """)
        self.later_btn.clicked.connect(self.reject)
        
        # Zorunlu ise Sonra butonunu gizle
        if self.update_info.force:
            self.later_btn.setVisible(False)
        
        btn_layout.addWidget(self.later_btn)
        
        btn_layout.addStretch()
        
        # Güncelle buton
        self.update_btn = QPushButton("🚀 Güncelle")
        self.update_btn.setFixedWidth(150)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4299e1, stop:1 #48bb78);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3182ce, stop:1 #38a169);
            }
            QPushButton:disabled {
                background: #4a5568;
            }
        """)
        self.update_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self.update_btn)
        
        layout.addLayout(btn_layout)
        
        # Dialog stili
        self.setStyleSheet("""
            QDialog {
                background: #1a202c;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
            }
        """)
    
    def _start_download(self):
        """İndirmeyi başlat - Versiyonlu klasörden"""
        self.update_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.progress_frame.setVisible(True)
        
        # Temp klasör oluştur
        self.temp_dir = Path(tempfile.gettempdir()) / "atmo_erp_update"
        
        # Download thread başlat - Versiyon klasöründen indir
        self.download_thread = DownloadThread(self.version_source_path, str(self.temp_dir))
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.start()
    
    def _on_progress(self, percent: int, message: str):
        """Progress güncellemesi"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
    
    def _on_download_finished(self, success: bool, message: str):
        """İndirme tamamlandı"""
        if success:
            self.progress_label.setText("Güncelleme uygulanıyor...")
            QTimer.singleShot(500, lambda: self._apply_update(message))
        else:
            QMessageBox.critical(self, "Hata", f"İndirme başarısız:\n{message}")
            self.update_btn.setEnabled(True)
            if not self.update_info.force:
                self.later_btn.setEnabled(True)
            self.progress_frame.setVisible(False)
    
    def _apply_update(self, temp_path: str):
        """Güncellemeyi uygula - BAT dosyası ile"""
        try:
            # Mevcut exe path
            if getattr(sys, 'frozen', False):
                # PyInstaller ile paketlenmiş
                current_exe = Path(sys.executable)
                app_dir = current_exe.parent
            else:
                # Development modunda
                QMessageBox.information(
                    self, "Geliştirici Modu", 
                    "Geliştirici modunda güncelleme simüle edildi.\n"
                    f"Dosyalar: {temp_path}"
                )
                self.accept()
                return
            
            # Path'leri string olarak al ve normalize et
            temp_path_str = str(Path(temp_path).resolve())
            app_dir_str = str(app_dir.resolve())
            exe_path_str = str(current_exe.resolve())
            
            # Update script oluştur
            bat_path = Path(tempfile.gettempdir()) / "atmo_update.bat"
            
            # BAT içeriği - değişkenler ayrı satırda set edilecek
            # EXE dosya adını path'ten al
            exe_name = current_exe.name

            bat_content = f'''@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ==============================================================
echo          NEXOR ERP Guncelleniyor...
echo          Versiyon: {self.update_info.version}
echo ==============================================================
echo.

:: Degiskenleri ayarla
set "TEMP_PATH={temp_path_str}"
set "APP_DIR={app_dir_str}"
set "EXE_PATH={exe_path_str}"
set "EXE_NAME={exe_name}"

echo Kaynak: %TEMP_PATH%
echo Hedef:  %APP_DIR%
echo.

:: Ana uygulama kapanmasini bekle
echo [1/4] Uygulama kapatiliyor...
echo        Bekleniyor...

:: Uygulamanin kapanmasini bekle (maks 30 saniye)
set RETRY=0
:wait_loop
tasklist /FI "IMAGENAME eq %EXE_NAME%" 2>NUL | find /I "%EXE_NAME%" >NUL
if "%ERRORLEVEL%"=="0" (
    set /a RETRY+=1
    if !RETRY! GEQ 10 (
        echo        Uygulama hala calisiyor, zorla kapatiliyor...
        taskkill /F /IM "%EXE_NAME%" >nul 2>&1
        timeout /t 3 /nobreak >nul
        goto :wait_done
    )
    timeout /t 3 /nobreak >nul
    goto :wait_loop
)
:wait_done
echo        [OK] Uygulama kapatildi

:: Eski _internal klasorunu sil
echo [2/4] Eski dosyalar temizleniyor...
if exist "%APP_DIR%\\_internal" (
    rmdir /S /Q "%APP_DIR%\\_internal"
    echo        _internal silindi
)

:: Dosyalari kopyala (retry ile)
echo [3/4] Yeni dosyalar kopyalaniyor...
echo.

set COPY_OK=0
for /L %%i in (1,1,5) do (
    if !COPY_OK!==0 (
        xcopy "%TEMP_PATH%\\*" "%APP_DIR%\\" /E /Y /I /Q >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set COPY_OK=1
        ) else (
            echo        Deneme %%i basarisiz, tekrar deneniyor...
            timeout /t 3 /nobreak >nul
        )
    )
)

if %COPY_OK% EQU 1 (
    echo.
    echo [OK] Guncelleme basariyla tamamlandi!
    echo.
    echo [4/4] Uygulama yeniden baslatiliyor...
    timeout /t 2 /nobreak >nul

    :: Uygulamayi baslat
    start "" "%EXE_PATH%"

    :: Temp dosyalari temizle
    rmdir /S /Q "%TEMP_PATH%" >nul 2>&1
) else (
    echo.
    echo [HATA] Dosyalar kopyalanamadi!
    echo.
    echo Kaynak klasor icerik:
    dir "%TEMP_PATH%" /B
    echo.
    echo Lutfen uygulamayi manuel olarak kapatin ve tekrar deneyin.
    echo.
    pause
)

:: Batch dosyasini sil
del "%~f0" >nul 2>&1
'''
            
            # ANSI encoding ile yaz (Türkçe karakter sorunu için)
            with open(bat_path, 'w', encoding='cp857') as f:
                f.write(bat_content)
            
            # BAT'ı başlat ve çık
            subprocess.Popen(
                ['cmd', '/c', str(bat_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Uygulamayı kapat
            QApplication.quit()
            sys.exit(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme uygulanamadı:\n{e}")
            self.update_btn.setEnabled(True)
            if not self.update_info.force:
                self.later_btn.setEnabled(True)
    
    def closeEvent(self, event):
        """Dialog kapanırken"""
        # Zorunlu güncelleme ise kapatmaya izin verme
        if self.update_info.force:
            event.ignore()
            QMessageBox.warning(
                self, "Zorunlu Güncelleme",
                "Bu güncelleme zorunludur!\n"
                "Uygulamayı kullanmak için güncelleme yapmanız gerekmektedir."
            )
            return
        
        # İndirme devam ediyorsa iptal et
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        
        event.accept()


class SelfUpdater:
    r"""
    Ana güncelleme yöneticisi - Versiyonlu yapı için.

    Yapı:
        \\AtlasNAS\Atmo_Logic\
        ├── versions\
        │   ├── 1.0.0\
        │   │   ├── Redline NexorERP.exe
        │   │   ├── version.json
        │   │   └── _internal\
        │   └── 1.0.1\
        └── latest.txt
    """
    
    def __init__(self):
        from version import VERSION
        from config import NAS_PATHS

        self.current_version = VERSION
        self.update_server = Path(NAS_PATHS["update_server"])
        self.update_info: Optional[UpdateInfo] = None
        self.version_source_path: Optional[str] = None
    
    def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Sunucudan güncelleme kontrolü yap - Versiyonlu yapı.
        
        Returns:
            UpdateInfo: Güncelleme varsa bilgiler, yoksa None
        """
        try:
            # 1) latest.txt dosyasını oku
            latest_file = self.update_server / "latest.txt"
            
            if not latest_file.exists():
                print(f"[Updater] latest.txt bulunamadı: {latest_file}")
                # Eski yapı ile uyumluluk: doğrudan version.json kontrol et
                return self._check_legacy_update()
            
            latest_version = latest_file.read_text(encoding='utf-8').strip()
            print(f"[Updater] Sunucudaki son versiyon: {latest_version}")
            
            # 2) Versiyon karşılaştır
            from version import compare_versions
            
            if compare_versions(self.current_version, latest_version) >= 0:
                print(f"[Updater] Güncel versiyon: {self.current_version}")
                return None
            
            # 3) Yeni versiyon var, version.json'ı oku
            version_dir = self.update_server / "versions" / latest_version
            version_json = version_dir / "version.json"
            
            if not version_json.exists():
                print(f"[Updater] version.json bulunamadı: {version_json}")
                # version.json olmasa bile güncelleme yapılabilir
                self.update_info = UpdateInfo({
                    'version': latest_version,
                    'changelog': f'Versiyon {latest_version}'
                }, latest_version)
            else:
                with open(version_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.update_info = UpdateInfo(data, latest_version)
            
            # Kaynak yolu kaydet
            self.version_source_path = str(version_dir)
            
            print(f"[Updater] Yeni versiyon bulundu: {latest_version}")
            print(f"[Updater] Kaynak: {self.version_source_path}")
            print(f"[Updater] Zorunlu: {self.update_info.force}")
            
            return self.update_info
            
        except FileNotFoundError as e:
            print(f"[Updater] Sunucuya erişilemiyor: {e}")
            return None
        except Exception as e:
            print(f"[Updater] Güncelleme kontrolü hatası: {e}")
            return None
    
    def _check_legacy_update(self) -> Optional[UpdateInfo]:
        """Eski yapı ile uyumluluk - doğrudan version.json kontrolü"""
        try:
            version_path = self.update_server / "version.json"
            
            if not version_path.exists():
                return None
            
            with open(version_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            server_version = data.get('version', '0.0.0')
            
            from version import compare_versions
            
            if compare_versions(self.current_version, server_version) < 0:
                self.update_info = UpdateInfo(data)
                self.version_source_path = str(self.update_server)
                print(f"[Updater] Eski yapı - Yeni versiyon: {server_version}")
                return self.update_info
            
            return None
            
        except Exception as e:
            print(f"[Updater] Eski yapı kontrolü hatası: {e}")
            return None
    
    def show_update_dialog(self, parent=None) -> bool:
        """
        Güncelleme dialog'unu göster.
        
        Returns:
            True: Güncelleme yapıldı (uygulama kapanacak)
            False: Kullanıcı erteledi
        """
        if not self.update_info or not self.version_source_path:
            return False
        
        dialog = UpdateDialog(
            self.update_info, 
            self.current_version, 
            self.version_source_path,
            parent
        )
        result = dialog.exec()
        
        return result == QDialog.Accepted
    
    def check_and_prompt(self, parent=None) -> bool:
        """
        Tek çağrıda kontrol et ve gerekirse dialog göster.
        
        Returns:
            True: Güncelleme işlemi başlatıldı
            False: Güncelleme yok veya ertelendi
        """
        update_info = self.check_for_updates()
        
        if update_info:
            return self.show_update_dialog(parent)
        
        return False


# Test için
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test UpdateInfo
    test_info = UpdateInfo({
        'version': '1.2.0',
        'build_date': '2025-01-20',
        'force': True,  # Zorunlu güncelleme testi
        'changelog': '• Versiyonlu deploy sistemi\n• Bug fix: Güncelleme hatası\n• Performans iyileştirmesi'
    })
    
    dialog = UpdateDialog(test_info, '1.0.0', r'\\AtlasNAS\Atmo_Logic\versions\1.2.0')
    dialog.exec()
