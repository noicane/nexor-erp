# -*- coding: utf-8 -*-
"""
NEXOR ERP - Build Manager GUI v7
=====================================
NEXOR için özel versiyonlu deploy sistemi.

DÜZELTMELER:
- Spec dosyası ismi otomatik algılanıyor
- version.py ve config.json otomatik spec'e ekleniyor
- EXE ismi proje isminden alınıyor
- Deploy path kontrolü iyileştirildi

Kullanım:
    python build_manager_v7_nexor.py
"""

import os
import sys
import json
import shutil
import subprocess
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QGroupBox, QFileDialog, QProgressBar, QFrame, QMessageBox,
    QGridLayout, QSplitter, QSpinBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QFont, QTextCursor, QIcon


# ============================================================
# SPEC ANALYZER - Otomatik spec güncelleme
# ============================================================

class SpecAnalyzer:
    """Proje klasörünü analiz edip spec dosyasını günceller"""
    
    # Standart olarak dahil edilmesi gereken klasörler
    STANDARD_FOLDERS = {'core', 'components', 'pages', 'dialogs', 'assets', 'utils'}
    
    # Yok sayılacak klasörler
    IGNORE_FOLDERS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 
        'dist', 'build', 'pybuild', '.idea', '.vscode',
        'node_modules', 'docs', 'tests', 'test', 'install'
    }
    
    # Yok sayılacak dosyalar
    IGNORE_FILES = {'__init__.py', 'setup.py', 'conftest.py'}
    
    # Standart kütüphaneler (hiddenimport'a eklenmez)
    STDLIB_MODULES = {
        'os', 'sys', 'json', 'pathlib', 'datetime', 'time', 're', 
        'typing', 'collections', 'functools', 'itertools', 'math',
        'hashlib', 'threading', 'subprocess', 'tempfile', 'shutil',
        'copy', 'gc', 'traceback', 'logging', 'configparser', 'csv',
        'io', 'pickle', 'sqlite3', 'abc', 'enum', 'dataclasses',
        'contextlib', 'warnings', 'weakref', 'operator', 'string'
    }
    
    # Zaten dahil olan paketler (spec'te var)
    INCLUDED_PACKAGES = {
        'PySide6', 'pyodbc', 'pandas', 'openpyxl'
    }
    
    def __init__(self, project_path: Path, spec_file: Path):
        self.project_path = project_path
        self.spec_file = spec_file
    
    def ensure_critical_files_in_spec(self) -> bool:
        """version.py ve config.json'ın spec'te olduğundan emin ol"""
        if not self.spec_file.exists():
            return False
        
        content = self.spec_file.read_text(encoding='utf-8')
        
        # version.py kontrolü
        if "('version.py', '.')" not in content and "'version.py'" not in content:
            # datas listesini bul ve version.py ekle
            datas_pattern = r"(datas\s*=\s*\[)(.*?)(\])"
            match = re.search(datas_pattern, content, re.DOTALL)
            if match:
                datas_content = match.group(2)
                # Son satırdan önce ekle
                lines = datas_content.strip().split('\n')
                if lines[-1].strip().endswith(','):
                    new_line = "        ('version.py', '.'),"
                else:
                    new_line = ",\n        ('version.py', '.'),"
                
                new_datas = datas_content.rstrip() + new_line
                content = content.replace(match.group(2), new_datas)
        
        # config.json kontrolü (muhtemelen zaten var ama kontrol et)
        if "('config.json', '.')" not in content and "'config.json'" not in content:
            datas_pattern = r"(datas\s*=\s*\[)(.*?)(\])"
            match = re.search(datas_pattern, content, re.DOTALL)
            if match:
                datas_content = match.group(2)
                lines = datas_content.strip().split('\n')
                if lines[-1].strip().endswith(','):
                    new_line = "        ('config.json', '.'),"
                else:
                    new_line = ",\n        ('config.json', '.'),"
                
                new_datas = datas_content.rstrip() + new_line
                content = content.replace(match.group(2), new_datas)
        
        # Güncellenmiş içeriği kaydet
        self.spec_file.write_text(content, encoding='utf-8')
        return True


# ============================================================
# VERSION MANAGER - Versiyonlu Deploy Sistemi
# ============================================================

class VersionManager:
    """
    Versiyonlu deploy sistemi.
    
    Klasör Yapısı:
        \\\\AtlasNAS\\Atmo_Logic\\
            versions/
                1.0.0/
                    NexorERP.exe
                    ...
                1.0.1/
                    NexorERP.exe
                    ...
            installer/
                NexorERP_Kur.bat
                NexorERP_Kaldir.bat
            latest.txt  -> "1.0.1"
    """
    
    MAX_VERSIONS = 3  # Maksimum saklanacak versiyon sayısı
    
    def __init__(self, base_path: str, log_func=None):
        self.base_path = Path(base_path)
        self.versions_dir = self.base_path / "versions"
        self.installer_dir = self.base_path / "installer"
        self.latest_file = self.base_path / "latest.txt"
        self.log = log_func or print
    
    def setup_structure(self) -> bool:
        """Klasör yapısını oluştur"""
        try:
            self.versions_dir.mkdir(parents=True, exist_ok=True)
            self.installer_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"   ✅ Klasör yapısı hazır", "green")
            return True
        except Exception as e:
            self.log(f"   ❌ Klasör yapısı oluşturulamadı: {e}", "red")
            return False
    
    def get_existing_versions(self) -> List[str]:
        """Mevcut versiyonları listele (sıralı)"""
        if not self.versions_dir.exists():
            return []
        
        versions = []
        for item in self.versions_dir.iterdir():
            if item.is_dir() and re.match(r'^\d+\.\d+\.\d+$', item.name):
                versions.append(item.name)
        
        # Semantic versioning ile sırala
        def version_key(v):
            parts = v.split('.')
            return tuple(int(p) for p in parts)
        
        return sorted(versions, key=version_key)
    
    def get_latest_version(self) -> Optional[str]:
        """En son versiyonu oku"""
        if self.latest_file.exists():
            return self.latest_file.read_text(encoding='utf-8').strip()
        return None
    
    def deploy_version(self, source_dir: Path, version: str) -> bool:
        """
        Yeni versiyonu deploy et.
        
        Args:
            source_dir: Build çıktı klasörü (dist/NexorERP)
            version: Versiyon numarası (örn: "2.0.0")
        
        Returns:
            Başarılı ise True
        """
        try:
            # Klasör yapısını oluştur
            if not self.setup_structure():
                return False
            
            # Hedef versiyon klasörü
            version_dir = self.versions_dir / version
            
            # Aynı versiyon zaten varsa sil
            if version_dir.exists():
                self.log(f"   ⚠️ Mevcut {version} siliniyor...", "yellow")
                shutil.rmtree(version_dir)
            
            # Dosyaları kopyala
            self.log(f"   📦 Versiyon {version} kopyalanıyor...", "cyan")
            shutil.copytree(source_dir, version_dir)
            
            # Kopyalanan dosya sayısını hesapla
            file_count = sum(1 for _ in version_dir.rglob('*') if _.is_file())
            total_size = sum(f.stat().st_size for f in version_dir.rglob('*') if f.is_file())
            total_mb = total_size / (1024 * 1024)
            
            self.log(f"   ✅ {file_count} dosya kopyalandı ({total_mb:.1f} MB)", "green")
            
            # latest.txt güncelle
            self.latest_file.write_text(version, encoding='utf-8')
            self.log(f"   📌 latest.txt güncellendi: {version}", "cyan")
            
            # Eski versiyonları temizle
            self._cleanup_old_versions()
            
            return True
            
        except PermissionError as e:
            self.log(f"   ❌ Erişim hatası: {e}", "red")
            self.log(f"   💡 Dosyalar kullanımda olabilir, uygulamayı kapatın", "yellow")
            return False
        except Exception as e:
            self.log(f"   ❌ Deploy hatası: {e}", "red")
            return False
    
    def _cleanup_old_versions(self):
        """Eski versiyonları sil (MAX_VERSIONS'dan fazlasını)"""
        versions = self.get_existing_versions()
        
        if len(versions) <= self.MAX_VERSIONS:
            return
        
        # En eski versiyonları sil
        to_delete = versions[:-self.MAX_VERSIONS]
        
        for version in to_delete:
            version_dir = self.versions_dir / version
            try:
                self.log(f"   🗑️ Eski versiyon siliniyor: {version}", "gray")
                shutil.rmtree(version_dir)
                self.log(f"   ✓ {version} silindi", "gray")
            except Exception as e:
                self.log(f"   ⚠️ {version} silinemedi: {e}", "yellow")
    
    def update_installers(self, kur_bat_content: str, kaldir_bat_content: str, exe_name: str):
        """Installer batch dosyalarını güncelle"""
        try:
            # Exe isminden bat isimleri oluştur
            base_name = exe_name.replace('.exe', '')
            kur_path = self.installer_dir / f"{base_name}_Kur.bat"
            kaldir_path = self.installer_dir / f"{base_name}_Kaldir.bat"
            
            kur_path.write_text(kur_bat_content, encoding='cp1254')
            kaldir_path.write_text(kaldir_bat_content, encoding='cp1254')
            
            self.log(f"   ✅ Installer dosyaları güncellendi", "green")
            return True
        except Exception as e:
            self.log(f"   ⚠️ Installer güncellenemedi: {e}", "yellow")
            return False


# ============================================================
# RELEASE MANAGER - Slot Pattern Deploy Sistemi (yeni)
# ============================================================

class ReleaseManager:
    """
    Slot pattern deploy sistemi - VersionManager'in modern hali.

    Klasor Yapisi:
        \\\\AtlasNAS\\Atmo_Logic\\
            releases/
                4.4.0/
                    NexorERP.exe
                    _internal/
                    version.json
                4.4.1/
                current.txt   -> "4.4.1"
            launcher/
                NexorSetup.exe   (Inno Setup installer)

    Mevcut versions/ klasoru bozulmaz - paralel calisir.
    """

    MAX_RELEASES = 5  # Sunucuda en fazla 5 surum tutulur

    def __init__(self, base_path: str, log_func=None):
        self.base_path = Path(base_path)
        self.releases_dir = self.base_path / "releases"
        self.launcher_dir = self.base_path / "launcher"
        self.current_file = self.releases_dir / "current.txt"
        self.log = log_func or print

    def setup_structure(self) -> bool:
        try:
            self.releases_dir.mkdir(parents=True, exist_ok=True)
            self.launcher_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.log(f"   ❌ releases/ klasoru olusturulamadi: {e}", "red")
            return False

    def get_existing_releases(self) -> List[str]:
        if not self.releases_dir.exists():
            return []
        out = []
        for item in self.releases_dir.iterdir():
            if item.is_dir() and re.match(r'^\d+\.\d+\.\d+$', item.name):
                out.append(item.name)
        return sorted(out, key=lambda v: tuple(int(x) for x in v.split('.')))

    def get_current_release(self) -> Optional[str]:
        if self.current_file.exists():
            return self.current_file.read_text(encoding='utf-8').strip()
        return None

    def deploy_release(self, source_dir: Path, version: str) -> bool:
        """
        Yeni surumu releases/X.Y.Z/ olarak yayinla + current.txt guncelle.
        Atomic yazim: once .tmp'e kopyala -> rename.
        """
        try:
            if not self.setup_structure():
                return False

            target_final = self.releases_dir / version
            target_tmp = self.releases_dir / f"{version}.tmp"

            # Eski tmp temizle
            if target_tmp.exists():
                shutil.rmtree(target_tmp, ignore_errors=True)

            # Aynisi varsa uyari
            if target_final.exists():
                self.log(f"   ⚠️ Mevcut release {version} silinecek...", "yellow")
                shutil.rmtree(target_final)

            self.log(f"   📦 Release {version} kopyalaniyor (atomic)...", "cyan")
            shutil.copytree(source_dir, target_tmp)

            # Atomic rename
            target_tmp.rename(target_final)

            file_count = sum(1 for _ in target_final.rglob('*') if _.is_file())
            total_mb = sum(f.stat().st_size for f in target_final.rglob('*') if f.is_file()) / (1024 * 1024)
            self.log(f"   ✅ {file_count} dosya, {total_mb:.1f} MB", "green")

            # current.txt guncelle (atomic: tmp + rename)
            cur_tmp = self.releases_dir / "current.txt.tmp"
            cur_tmp.write_text(version, encoding='utf-8')
            if self.current_file.exists():
                self.current_file.unlink()
            cur_tmp.rename(self.current_file)
            self.log(f"   📌 current.txt -> {version}", "cyan")

            self._cleanup_old_releases(version)
            return True

        except PermissionError as e:
            self.log(f"   ❌ Erisim hatasi: {e}", "red")
            return False
        except Exception as e:
            self.log(f"   ❌ Release deploy hatasi: {e}", "red")
            return False

    def _cleanup_old_releases(self, current_version: str):
        """Sunucuda MAX_RELEASES'dan fazlasini sil. Aktif surum kesinlikle silinmez."""
        releases = self.get_existing_releases()
        if len(releases) <= self.MAX_RELEASES:
            return

        # En eskileri sil, ama aktif olanlari ASLA silme
        to_delete = releases[:-self.MAX_RELEASES]
        for v in to_delete:
            if v == current_version:
                continue
            try:
                shutil.rmtree(self.releases_dir / v)
                self.log(f"   🗑️ Eski release silindi: {v}", "gray")
            except Exception as e:
                self.log(f"   ⚠️ {v} silinemedi: {e}", "yellow")

    def deploy_launcher(self, launcher_exe: Path, installer_exe: Optional[Path] = None) -> bool:
        """Launcher exe ve (varsa) Inno Setup installer'ini launcher/ altina kopyala."""
        try:
            if not self.setup_structure():
                return False
            shutil.copy2(launcher_exe, self.launcher_dir / launcher_exe.name)
            self.log(f"   ✅ Launcher kopyalandi: {launcher_exe.name}", "green")
            if installer_exe and installer_exe.exists():
                shutil.copy2(installer_exe, self.launcher_dir / installer_exe.name)
                self.log(f"   ✅ Installer kopyalandi: {installer_exe.name}", "green")
            return True
        except Exception as e:
            self.log(f"   ❌ Launcher deploy hatasi: {e}", "red")
            return False


# ============================================================
# BUILD WORKER
# ============================================================

class BuildWorker(QThread):
    """Build ve Deploy işlemleri için Worker Thread"""

    log_signal = Signal(str, str)  # message, color
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)  # success, message

    def __init__(self, project_path: str, action: str, config: dict):
        super().__init__()
        self.project_path = Path(project_path)
        self.action = action
        self.config = config
        self._cancelled = False

        # Doğru Python yorumlayıcısını bul (Windows Store değil, asıl kurulum)
        self.python_exe = self._find_best_python()

        # Build modu
        self.onefile = config.get('onefile', False)

        # Slot pattern modu (yeni releases/ deploy)
        self.slot_pattern = config.get('slot_pattern', False)

        # Launcher build action ise farkli spec kullan
        if self.action == 'build_launcher':
            launcher_spec = self.project_path / 'launcher' / 'nexor_launcher.spec'
            if not launcher_spec.exists():
                raise ValueError(f"Launcher spec bulunamadi: {launcher_spec}")
            self.spec_file = launcher_spec
            self.exe_name = 'NexorLauncher.exe'
            self.dist_folder_name = 'NexorLauncher'
        else:
            # Spec dosyasını bul (moduna göre)
            self.spec_file = self._find_spec_file()
            if not self.spec_file:
                raise ValueError("Spec dosyası bulunamadı!")

            # EXE ismini spec'ten al
            self.exe_name = self._get_exe_name_from_spec()
            self.dist_folder_name = self.exe_name.replace('.exe', '')
    
    def _find_best_python(self) -> str:
        """
        Doğru Python yorumlayıcısını bul.
        PyInstaller + pyodbc kurulu olan Programs Python'u tercih et.
        Windows Store Python paket eksikleri nedeniyle sorun çıkarabilir.
        """
        import glob

        # Programs altındaki Python kurulumlarını ara
        candidates = glob.glob(r"C:\Users\*\AppData\Local\Programs\Python\Python3*\python.exe")

        # Her adayda PyInstaller + pyodbc olup olmadığını kontrol et
        for candidate in sorted(candidates, reverse=True):
            if not os.path.exists(candidate):
                continue
            try:
                result = subprocess.run(
                    [candidate, '-c', 'import PyInstaller, pyodbc'],
                    capture_output=True, timeout=10
                )
                if result.returncode == 0:
                    return candidate
            except Exception:
                continue

        # Bulunamazsa mevcut yorumlayıcıyı kullan
        return sys.executable

    def _find_spec_file(self) -> Optional[Path]:
        """Proje klasöründe .spec dosyasını bul (build moduna göre)"""
        if self.onefile:
            # Önce _OneFile spec'ini ara
            for file in self.project_path.glob("*_OneFile.spec"):
                return file
            for file in self.project_path.glob("*_onefile.spec"):
                return file
        # Normal (one-folder) spec dosyasını bul
        for file in self.project_path.glob("*.spec"):
            if '_OneFile' not in file.name and '_onefile' not in file.name:
                return file
        # Fallback: herhangi bir spec
        for file in self.project_path.glob("*.spec"):
            return file
        return None
    
    def _get_exe_name_from_spec(self) -> str:
        """Spec dosyasından EXE ismini al"""
        if not self.spec_file:
            return "App.exe"
        
        content = self.spec_file.read_text(encoding='utf-8')
        # EXE() bloğunda name parametresini ara
        match = re.search(r"EXE\([^)]*name\s*=\s*['\"]([^'\"]+)['\"]", content, re.DOTALL)
        if match:
            exe_name = match.group(1)
            if not exe_name.endswith('.exe'):
                exe_name += '.exe'
            return exe_name
        
        # Bulunamazsa spec dosya isminden tahmin et
        return self.spec_file.stem + ".exe"
    
    def cancel(self):
        self._cancelled = True
    
    def log(self, message: str, color: str = "white"):
        self.log_signal.emit(message, color)
    
    def run(self):
        try:
            # ===== Launcher Build (ozel akis) =====
            if self.action == 'build_launcher':
                self.log(f"📋 Launcher Build: {self.spec_file.name}", "cyan")
                self.log(f"🐍 Python: {self.python_exe}", "cyan")
                self.progress_signal.emit(10)

                if not self._run_build():
                    self.finished_signal.emit(False, "Launcher build başarısız!")
                    return

                self.progress_signal.emit(70)

                # Launcher'i sunucuya kopyala (slot pattern modunda)
                if self.config.get('deploy_path'):
                    self.log("\n📤 Launcher sunucuya yukleniyor...", "cyan")
                    self.progress_signal.emit(85)
                    if not self._deploy_launcher():
                        self.finished_signal.emit(False, "Launcher deploy basarisiz!")
                        return

                self.progress_signal.emit(100)
                self.log("\n" + "="*50, "green")
                self.log("✅ Launcher hazir!", "green")
                self.log("="*50, "green")
                self.finished_signal.emit(True, "Launcher tamamlandi!")
                return

            # ===== Normal Build/Deploy =====
            if self.action in ('build', 'build_deploy'):
                # Build modu bilgisi
                mode_str = "TEK EXE (One-File)" if self.onefile else "Çoklu Dosya (One-Folder)"
                self.log(f"📋 Build Modu: {mode_str}", "cyan")
                self.log(f"📋 Spec Dosyası: {self.spec_file.name}", "cyan")
                self.log(f"🐍 Python: {self.python_exe}", "cyan")
                if self.slot_pattern:
                    self.log(f"🆕 Slot Pattern Deploy: AKTIF (releases/)", "cyan")

                # Versiyon güncelle
                if self.config.get('bump_type'):
                    self.log("📝 Versiyon güncelleniyor...", "cyan")
                    self.progress_signal.emit(5)
                    old_ver, new_ver = self._bump_version()
                    self.log(f"   {old_ver} → {new_ver}", "green")

                # Spec'e critical dosyaları ekle
                self.log("🔧 Spec dosyası kontrol ediliyor...", "cyan")
                analyzer = SpecAnalyzer(self.project_path, self.spec_file)
                if analyzer.ensure_critical_files_in_spec():
                    self.log("   ✅ version.py ve config.json spec'e eklendi", "green")

                # Build
                self.log("\n🔨 PyInstaller başlatılıyor...", "cyan")
                self.progress_signal.emit(10)

                if not self._run_build():
                    self.finished_signal.emit(False, "Build başarısız!")
                    return

                self.progress_signal.emit(70)

                # version.json oluştur
                self.log("\n📄 version.json oluşturuluyor...", "cyan")
                self._create_version_json()
                self.progress_signal.emit(80)

            if self.action in ('deploy', 'build_deploy'):
                # Deploy - slot pattern aktifse releases/ kullan
                self.log("\n📤 Sunucuya yükleniyor...", "cyan")
                self.progress_signal.emit(85)

                if self.slot_pattern:
                    if not self._deploy_slot():
                        self.finished_signal.emit(False, "Slot deploy başarısız!")
                        return
                else:
                    if not self._deploy():
                        self.finished_signal.emit(False, "Deploy başarısız!")
                        return

                self.progress_signal.emit(100)

            self.log("\n" + "="*50, "green")
            self.log("✅ İşlem başarıyla tamamlandı!", "green")
            self.log("="*50, "green")
            self.finished_signal.emit(True, "Tamamlandı!")

        except Exception as e:
            self.log(f"\n❌ Hata: {e}", "red")
            self.finished_signal.emit(False, str(e))
    
    def _bump_version(self) -> Tuple[str, str]:
        """Versiyon güncelle"""
        version_file = self.project_path / "version.py"
        content = version_file.read_text(encoding='utf-8')
        
        major = int(re.search(r'VERSION_MAJOR\s*=\s*(\d+)', content).group(1))
        minor = int(re.search(r'VERSION_MINOR\s*=\s*(\d+)', content).group(1))
        patch = int(re.search(r'VERSION_PATCH\s*=\s*(\d+)', content).group(1))
        build = int(re.search(r'BUILD_NUMBER\s*=\s*(\d+)', content).group(1))
        
        old_version = f"{major}.{minor}.{patch}"
        bump_type = self.config.get('bump_type')
        
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'patch':
            patch += 1
        
        build += 1
        new_version = f"{major}.{minor}.{patch}"
        
        # Güncelle
        content = re.sub(r'VERSION = "[^"]+"', f'VERSION = "{new_version}"', content)
        content = re.sub(r'VERSION_MAJOR = \d+', f'VERSION_MAJOR = {major}', content)
        content = re.sub(r'VERSION_MINOR = \d+', f'VERSION_MINOR = {minor}', content)
        content = re.sub(r'VERSION_PATCH = \d+', f'VERSION_PATCH = {patch}', content)
        content = re.sub(r'BUILD_NUMBER = \d+', f'BUILD_NUMBER = {build}', content)
        content = re.sub(
            r'BUILD_DATE = "[^"]+"', 
            f'BUILD_DATE = "{datetime.now().strftime("%Y-%m-%d")}"', 
            content
        )
        
        version_file.write_text(content, encoding='utf-8')
        
        # Config'e kaydet
        self.config['new_version'] = new_version
        self.config['build_number'] = build
        
        return old_version, new_version
    
    def _safe_rmtree(self, path: Path, max_retries=3) -> bool:
        """Güvenli klasör silme (retry ile)"""
        for attempt in range(max_retries):
            try:
                if path.exists():
                    shutil.rmtree(path)
                return True
            except PermissionError:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                else:
                    self.log(f"   ❌ {path.name} silinemedi (dosyalar kullanımda)", "red")
                    return False
        return True
    
    def _update_spec_icon(self, spec_file: Path, icon_path: str):
        """Spec dosyasındaki icon yolunu güncelle"""
        content = spec_file.read_text(encoding='utf-8')
        
        # Icon parametresini bul ve güncelle
        if "icon=" in content:
            content = re.sub(
                r"icon\s*=\s*['\"][^'\"]*['\"]",
                f"icon='{icon_path}'",
                content
            )
        else:
            # Icon parametresi yoksa EXE() bloğuna ekle
            content = re.sub(
                r"(EXE\([^)]+)",
                rf"\1,\n    icon='{icon_path}'",
                content,
                count=1
            )
        
        spec_file.write_text(content, encoding='utf-8')
    
    def _run_build(self) -> bool:
        """PyInstaller ile build yap"""
        spec_file = self.spec_file
        
        # Icon ayarla (spec dosyasını güncelle)
        icon_path = self.config.get('icon_path')
        if icon_path and Path(icon_path).exists():
            self._update_spec_icon(spec_file, icon_path)
            self.log(f"   🎨 Icon ayarlandı: {Path(icon_path).name}", "cyan")
        
        # Eski build'i temizle
        dist_path = self.project_path / "dist"
        pybuild_path = self.project_path / "pybuild"
        
        self.log("   🗑️ Eski build dosyaları temizleniyor...", "gray")
        
        if dist_path.exists():
            if not self._safe_rmtree(dist_path):
                return False
            self.log("   ✓ dist temizlendi", "gray")
        
        if pybuild_path.exists():
            if not self._safe_rmtree(pybuild_path):
                return False
            self.log("   ✓ pybuild temizlendi", "gray")
        
        # PyInstaller çalıştır
        self.log("   ⏳ PyInstaller çalışıyor (bu biraz sürebilir)...", "yellow")
        
        pybuild_path = self.project_path / "pybuild"
        
        self.log(f"   🐍 Python: {self.python_exe}", "gray")

        process = subprocess.Popen(
            [
                self.python_exe, '-m', 'PyInstaller',
                str(spec_file),
                '--noconfirm',
                '--clean',
                '--workpath', str(pybuild_path)
            ],
            cwd=str(self.project_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Çıktıyı oku
        for line in process.stdout:
            line = line.strip()
            if line:
                # Sadece önemli satırları göster
                if any(x in line.lower() for x in ['error', 'warning', 'building', 'copying', 'completed']):
                    if 'error' in line.lower():
                        self.log(f"   ❌ {line}", "red")
                    elif 'warning' in line.lower():
                        self.log(f"   ⚠️ {line}", "yellow")
                    else:
                        self.log(f"   {line}", "gray")
            
            if self._cancelled:
                process.terminate()
                return False
        
        process.wait()
        
        if process.returncode != 0:
            self.log("   ❌ PyInstaller hata ile sonlandı!", "red")
            return False
        
        # Build başarılı mı kontrol et
        if self.onefile:
            # One-file: exe doğrudan dist/ altında
            exe_file = self.project_path / "dist" / self.exe_name
            if not exe_file.exists():
                self.log(f"   ❌ EXE dosyası oluşturulamadı: {self.exe_name}", "red")
                self.log(f"   📁 Beklenen konum: {exe_file}", "yellow")
                return False

            size_mb = exe_file.stat().st_size / (1024 * 1024)
            self.log(f"   ✅ Tek EXE oluşturuldu: {size_mb:.1f} MB", "green")

            # One-file için dağıtım klasörü oluştur (deploy uyumluluğu)
            staging_dir = self.project_path / "dist" / self.dist_folder_name
            staging_dir.mkdir(parents=True, exist_ok=True)

            # EXE'yi staging klasörüne kopyala
            import shutil
            shutil.copy2(exe_file, staging_dir / self.exe_name)

            # config.json ve Nexor.UDL'yi de kopyala (exe yanında olmalı)
            for cfg_name in ['config.json', 'Nexor.UDL']:
                cfg_src = self.project_path / cfg_name
                if cfg_src.exists():
                    shutil.copy2(cfg_src, staging_dir / cfg_name)
                    self.log(f"   📄 {cfg_name} kopyalandı (exe yanına)", "gray")

            self.log(f"   📦 Dağıtım klasörü hazırlandı: {staging_dir.name}/", "cyan")
        else:
            # One-folder: exe dist/{name}/ altında
            dist_dir = self.project_path / "dist" / self.dist_folder_name
            exe_file = dist_dir / self.exe_name

            if not exe_file.exists():
                self.log(f"   ❌ EXE dosyası oluşturulamadı: {self.exe_name}", "red")
                self.log(f"   📁 Beklenen konum: {exe_file}", "yellow")
                return False

            size_mb = exe_file.stat().st_size / (1024 * 1024)
            self.log(f"   ✅ EXE oluşturuldu: {size_mb:.1f} MB", "green")

            total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
            total_mb = total_size / (1024 * 1024)
            self.log(f"   📦 Toplam boyut: {total_mb:.1f} MB", "cyan")

        return True
    
    def _create_version_json(self):
        """version.json oluştur"""
        dist_dir = self.project_path / "dist" / self.dist_folder_name
        
        version = self.config.get('new_version') or self._get_current_version()
        
        version_data = {
            "version": version,
            "build_date": datetime.now().strftime("%Y-%m-%d"),
            "build_number": self.config.get('build_number', 1),
            "force": self.config.get('force_update', False),
            "min_version": "1.0.0",
            "changelog": self.config.get('changelog', f"Versiyon {version}")
        }
        
        json_path = dist_dir / "version.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)
        
        self.log(f"   ✅ version.json oluşturuldu", "green")
    
    def _get_current_version(self) -> str:
        """Mevcut versiyonu oku"""
        version_file = self.project_path / "version.py"
        if not version_file.exists():
            return "1.0.0"
        
        content = version_file.read_text(encoding='utf-8')
        match = re.search(r'VERSION\s*=\s*"([\d.]+)"', content)
        return match.group(1) if match else "1.0.0"
    
    def _deploy(self) -> bool:
        """Versiyonlu deploy sistemi ile sunucuya deploy et"""
        deploy_path = self.config.get('deploy_path')
        if not deploy_path:
            self.log("   ❌ Deploy hedefi belirtilmedi", "red")
            return False
        
        dist_dir = self.project_path / "dist" / self.dist_folder_name
        
        if not dist_dir.exists():
            self.log(f"   ❌ Build klasörü bulunamadı: {dist_dir}", "red")
            return False
        
        # Versiyon al
        version = self.config.get('new_version') or self._get_current_version()
        
        # Version Manager oluştur
        vm = VersionManager(deploy_path, self.log)
        
        # Sunucu erişim kontrolü
        try:
            target = Path(deploy_path)
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
                self.log(f"   📁 Ana klasör oluşturuldu: {target}", "cyan")
        except Exception as e:
            self.log(f"   ❌ Sunucuya erişilemiyor: {e}", "red")
            self.log(f"   💡 Ağ bağlantınızı ve yolu kontrol edin: {deploy_path}", "yellow")
            return False
        
        # Mevcut versiyonları göster
        existing = vm.get_existing_versions()
        if existing:
            self.log(f"   📋 Mevcut versiyonlar: {', '.join(existing)}", "gray")
        
        # Deploy et
        self.log(f"   🚀 Versiyon {version} deploy ediliyor...", "cyan")
        
        if not vm.deploy_version(dist_dir, version):
            return False
        
        # Installer batch dosyalarını güncelle
        self.log("   📝 Installer dosyaları güncelleniyor...", "cyan")
        
        kur_content = self._generate_kur_bat(deploy_path)
        kaldir_content = self._generate_kaldir_bat()
        vm.update_installers(kur_content, kaldir_content, self.exe_name)
        
        self.log(f"   ✅ Deploy tamamlandı: {deploy_path}", "green")
        return True

    def _deploy_slot(self) -> bool:
        """Slot pattern: releases/X.Y.Z/ + current.txt + atomic write."""
        deploy_path = self.config.get('deploy_path')
        if not deploy_path:
            self.log("   ❌ Deploy hedefi belirtilmedi", "red")
            return False

        dist_dir = self.project_path / "dist" / self.dist_folder_name
        if not dist_dir.exists():
            self.log(f"   ❌ Build klasörü bulunamadı: {dist_dir}", "red")
            return False

        version = self.config.get('new_version') or self._get_current_version()
        rm = ReleaseManager(deploy_path, self.log)

        # Sunucu erisim
        try:
            target = Path(deploy_path)
            target.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log(f"   ❌ Sunucuya erisilemiyor: {e}", "red")
            return False

        existing = rm.get_existing_releases()
        current = rm.get_current_release()
        if existing:
            self.log(f"   📋 Mevcut releases: {', '.join(existing)}", "gray")
        if current:
            self.log(f"   📌 Aktif release: {current}", "gray")

        self.log(f"   🚀 Release {version} deploy ediliyor (slot pattern)...", "cyan")
        if not rm.deploy_release(dist_dir, version):
            return False

        self.log(f"   ✅ Slot deploy tamamlandi: {deploy_path}/releases/{version}", "green")
        return True

    def _deploy_launcher(self) -> bool:
        """Launcher exe'yi sunucudaki launcher/ klasorune kopyala."""
        deploy_path = self.config.get('deploy_path')
        if not deploy_path:
            return False

        # Launcher exe konumu
        if self.onefile:
            launcher_exe = self.project_path / "dist" / "NexorLauncher.exe"
        else:
            launcher_exe = self.project_path / "dist" / "NexorLauncher" / "NexorLauncher.exe"

        if not launcher_exe.exists():
            self.log(f"   ❌ Launcher exe bulunamadi: {launcher_exe}", "red")
            return False

        # Inno Setup ile uretilen installer (varsa)
        installer_exe = self.project_path / "dist" / "installer" / "NexorSetup.exe"

        rm = ReleaseManager(deploy_path, self.log)
        return rm.deploy_launcher(launcher_exe, installer_exe if installer_exe.exists() else None)

    def _generate_kur_bat(self, deploy_path: str) -> str:
        """Versiyonlu kurulum batch dosyası içeriği"""
        # Uygulama ismini al
        app_name = self.exe_name.replace('.exe', '')
        app_display_name = app_name.replace('ERP', ' ERP')  # "NexorERP" -> "Nexor ERP"
        
        # ÖZEL: NEXOR için C:\Nexor klasörü kullan
        install_folder = "Nexor"
        
        return f'''@echo off
setlocal EnableDelayedExpansion
REM UNC path desteği için pushd kullan
pushd "%~dp0"
title {app_display_name} - Kurulum
color 1F

echo.
echo  ===========================================================
echo            {app_display_name} - KURULUM
echo  ===========================================================
echo.

set "SOURCE={deploy_path}"
set "DEST=C:\\{install_folder}"
set "EXE_NAME={self.exe_name}"
set "SHORTCUT_NAME={app_display_name}"

echo  [1/6] Sunucu kontrol ediliyor...
if not exist "%SOURCE%\\latest.txt" (
    echo.
    echo  HATA: Sunucuya erisilemedi veya versiyon bulunamadi!
    echo  Kontrol edin:
    echo  - Ag baglantisi aktif mi?
    echo  - %SOURCE% erisilebilir mi?
    echo.
    pause
    exit /b 1
)
echo        [OK] Sunucu erisilebilir
echo.

echo  [2/6] En son versiyon belirleniyor...
set /p LATEST_VERSION=<"%SOURCE%\\latest.txt"
set "VERSION_PATH=%SOURCE%\\versions\\%LATEST_VERSION%"
echo        [OK] En son versiyon: %LATEST_VERSION%

if not exist "%VERSION_PATH%\\%EXE_NAME%" (
    echo.
    echo  HATA: Versiyon dosyalari bulunamadi: %VERSION_PATH%
    echo.
    pause
    exit /b 1
)
echo.

echo  [3/6] Eski versiyon kontrol ediliyor...
if exist "%DEST%" (
    echo        Eski versiyon bulundu, siliniyor...
    rd /s /q "%DEST%" 2>nul
    if exist "%DEST%" (
        echo.
        echo  UYARI: Eski versiyon silinemedi!
        echo  Lutfen uygulamayi kapatip tekrar deneyin.
        echo.
        pause
        exit /b 1
    )
)
echo        [OK] Hazir
echo.

echo  [4/6] Yeni versiyon kopyalaniyor...
echo        Kaynak: %VERSION_PATH%
echo        Hedef : %DEST%
echo.

REM Hedef klasörü oluştur
if not exist "%DEST%" mkdir "%DEST%"

REM robocopy kullan (daha güvenli, UNC path destekli)
robocopy "%VERSION_PATH%" "%DEST%" /E /R:3 /W:5 /NFL /NDL /NJH /NJS
if errorlevel 8 (
    echo.
    echo  HATA: Dosyalar kopyalanamadi! (Kod: %ERRORLEVEL%)
    echo.
    pause
    exit /b 1
)
echo        [OK] Dosyalar kopyalandi
echo.

echo  [5/6] Masaustu kisayolu olusturuluyor...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\\Desktop\\%SHORTCUT_NAME%.lnk'); $s.TargetPath = '%DEST%\\%EXE_NAME%'; $s.WorkingDirectory = '%DEST%'; $s.IconLocation = '%DEST%\\%EXE_NAME%,0'; $s.Save()"
if exist "%USERPROFILE%\\Desktop\\%SHORTCUT_NAME%.lnk" (
    echo        [OK] Kisayol olusturuldu
) else (
    echo        [UYARI] Kisayol olusturulamadi
)
echo.

echo  [6/6] Baslangic menusune ekleniyor...
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{app_display_name}" mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{app_display_name}"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{app_display_name}\\%SHORTCUT_NAME%.lnk'); $s.TargetPath = '%DEST%\\%EXE_NAME%'; $s.WorkingDirectory = '%DEST%'; $s.IconLocation = '%DEST%\\%EXE_NAME%,0'; $s.Save()"
echo        [OK] Baslangic menusune eklendi
echo.

echo  ===========================================================
echo               KURULUM TAMAMLANDI!
echo  ===========================================================
echo.
echo  Versiyon      : %LATEST_VERSION%
echo  Kurulum Yeri  : %DEST%
echo  Kisayol       : Masaustu
echo.
echo  Uygulamayi baslatmak icin masaustundeki kisayola tiklayin.
echo.
popd
pause
'''
    
    def _generate_kaldir_bat(self) -> str:
        """Kaldırma batch dosyası içeriği"""
        app_name = self.exe_name.replace('.exe', '')
        app_display_name = app_name.replace('ERP', ' ERP')
        
        # ÖZEL: NEXOR için C:\Nexor klasörü kullan
        install_folder = "Nexor"
        
        return f'''@echo off
title {app_display_name} - Kaldirma
color 4F

echo.
echo  ===========================================================
echo            {app_display_name} - KALDIRMA
echo  ===========================================================
echo.

set "DEST=C:\\{install_folder}"
set "SHORTCUT_NAME={app_display_name}"

echo  UYARI: Bu islem uygulamayi tamamen kaldiracaktir!
echo.
choice /C YN /M "Devam etmek istiyor musunuz (Y/N)"
if errorlevel 2 goto :cancel

echo.
echo  [1/3] Uygulama dosyalari siliniyor...
if exist "%DEST%" (
    rd /s /q "%DEST%"
    echo        [OK] Dosyalar silindi
) else (
    echo        [INFO] Uygulama zaten kurulu degil
)
echo.

echo  [2/3] Masaustu kisayolu siliniyor...
if exist "%USERPROFILE%\\Desktop\\%SHORTCUT_NAME%.lnk" (
    del "%USERPROFILE%\\Desktop\\%SHORTCUT_NAME%.lnk"
    echo        [OK] Kisayol silindi
) else (
    echo        [INFO] Kisayol bulunamadi
)
echo.

echo  [3/3] Baslangic menusunden kaldiriliyor...
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{app_display_name}" (
    rd /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{app_display_name}"
    echo        [OK] Baslangic menusu temizlendi
) else (
    echo        [INFO] Baslangic menusu kaydi bulunamadi
)
echo.

echo  ===========================================================
echo               KALDIRMA TAMAMLANDI!
echo  ===========================================================
echo.
pause
exit /b 0

:cancel
echo.
echo  Islem iptal edildi.
echo.
pause
exit /b 0
'''


# ============================================================
# GUI - Ana Pencere
# ============================================================

class BuildManagerGUI(QMainWindow):
    """Build Manager Ana Pencere"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEXOR ERP - Build Manager v7")
        self.setGeometry(100, 100, 1200, 800)
        
        self.project_path = None
        self.worker = None
        
        self._init_ui()
        self._apply_theme()
        self._load_settings()
    
    def _init_ui(self):
        """UI bileşenlerini oluştur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== Proje Ayarları =====
        project_group = QGroupBox("📁 Proje Ayarları")
        project_layout = QGridLayout()
        project_layout.setSpacing(10)
        
        # Proje klasörü
        project_layout.addWidget(QLabel("Proje Klasörü:"), 0, 0)
        self.project_path_edit = QLineEdit()
        project_layout.addWidget(self.project_path_edit, 0, 1)
        browse_project_btn = QPushButton("Gözat")
        browse_project_btn.clicked.connect(self._browse_project)
        project_layout.addWidget(browse_project_btn, 0, 2)
        
        # Deploy hedefi
        project_layout.addWidget(QLabel("Deploy Hedefi:"), 1, 0)
        self.deploy_path_edit = QLineEdit()
        self.deploy_path_edit.setPlaceholderText(r"\\AtlasNAS\Atmo_Logic")
        project_layout.addWidget(self.deploy_path_edit, 1, 1)
        browse_deploy_btn = QPushButton("Gözat")
        browse_deploy_btn.clicked.connect(self._browse_deploy)
        project_layout.addWidget(browse_deploy_btn, 1, 2)
        
        # Build modu
        project_layout.addWidget(QLabel("Build Modu:"), 2, 0)
        self.build_mode_combo = QComboBox()
        self.build_mode_combo.addItems([
            "Çoklu Dosya (One-Folder) - Hızlı başlangıç",
            "Tek EXE (One-File) - Taşınabilir"
        ])
        self.build_mode_combo.setToolTip(
            "Çoklu Dosya: Klasör + DLL'ler, hızlı açılır\n"
            "Tek EXE: Herşey tek dosyada, taşıması kolay ama açılışı yavaş"
        )
        project_layout.addWidget(self.build_mode_combo, 2, 1, 1, 2)

        # Icon dosyası
        project_layout.addWidget(QLabel("Icon Dosyası:"), 3, 0)
        self.icon_path_edit = QLineEdit()
        self.icon_path_edit.setPlaceholderText("assets/icon.ico")
        project_layout.addWidget(self.icon_path_edit, 3, 1)
        browse_icon_btn = QPushButton("Gözat")
        browse_icon_btn.clicked.connect(self._browse_icon)
        project_layout.addWidget(browse_icon_btn, 3, 2)
        
        project_group.setLayout(project_layout)
        main_layout.addWidget(project_group)
        
        # ===== Versiyon Ayarları =====
        version_group = QGroupBox("🔢 Versiyon Yönetimi")
        version_layout = QVBoxLayout()
        
        # Mevcut versiyon göstergesi
        current_version_layout = QHBoxLayout()
        current_version_layout.addWidget(QLabel("Mevcut Versiyon:"))
        self.current_version_label = QLabel("--")
        self.current_version_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4299e1;")
        current_version_layout.addWidget(self.current_version_label)
        current_version_layout.addStretch()
        version_layout.addLayout(current_version_layout)
        
        # Versiyon güncelleme satırı
        update_layout = QHBoxLayout()
        update_layout.addWidget(QLabel("Versiyon Güncellemesi:"))
        self.bump_type = QComboBox()
        self.bump_type.addItems(["Yok", "Patch (X.X.+1)", "Minor (X.+1.0)", "Major (+1.0.0)"])
        self.bump_type.currentIndexChanged.connect(self._update_version_preview)
        update_layout.addWidget(self.bump_type)
        
        # Yeni versiyon önizlemesi
        update_layout.addWidget(QLabel("→"))
        self.new_version_label = QLabel("--")
        self.new_version_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #48bb78;")
        update_layout.addWidget(self.new_version_label)
        
        update_layout.addWidget(QLabel("Changelog:"))
        self.changelog_edit = QLineEdit()
        self.changelog_edit.setPlaceholderText("Versiyon notları...")
        update_layout.addWidget(self.changelog_edit, stretch=2)
        
        self.force_update_check = QCheckBox("Zorunlu Güncelleme")
        update_layout.addWidget(self.force_update_check)

        version_layout.addLayout(update_layout)

        # Slot pattern (yeni deploy modu)
        slot_layout = QHBoxLayout()
        self.slot_pattern_check = QCheckBox("🆕 Slot Pattern Deploy (releases/) - YENI MIMARI")
        self.slot_pattern_check.setToolTip(
            "Yeni mimari: releases/X.Y.Z/ + current.txt yapisinda yayin yapar.\n"
            "Launcher otomatik indirir, calisan exe'ye dokunulmaz.\n"
            "Eski versions/ deploy bozulmaz - paralel calisir."
        )
        self.slot_pattern_check.setChecked(True)  # Yeni mimari default
        slot_layout.addWidget(self.slot_pattern_check)
        slot_layout.addStretch()
        version_layout.addLayout(slot_layout)

        version_group.setLayout(version_layout)
        main_layout.addWidget(version_group)
        
        # ===== Log Alanı =====
        log_group = QGroupBox("📋 İşlem Detayları")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        log_layout.addWidget(self.progress_bar)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, stretch=1)
        
        # ===== Butonlar =====
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.build_btn = QPushButton("🔨 Build")
        self.build_btn.setMinimumHeight(40)
        self.build_btn.clicked.connect(lambda: self._start_action('build'))
        btn_layout.addWidget(self.build_btn)
        
        self.deploy_btn = QPushButton("📤 Deploy")
        self.deploy_btn.setMinimumHeight(40)
        self.deploy_btn.clicked.connect(lambda: self._start_action('deploy'))
        btn_layout.addWidget(self.deploy_btn)
        
        self.build_deploy_btn = QPushButton("🚀 Build & Deploy")
        self.build_deploy_btn.setMinimumHeight(40)
        self.build_deploy_btn.clicked.connect(lambda: self._start_action('build_deploy'))
        btn_layout.addWidget(self.build_deploy_btn)

        self.launcher_btn = QPushButton("📦 Launcher Build")
        self.launcher_btn.setMinimumHeight(40)
        self.launcher_btn.setToolTip("NexorLauncher.exe build et + sunucuya kopyala (slot pattern)")
        self.launcher_btn.clicked.connect(lambda: self._start_action('build_launcher'))
        btn_layout.addWidget(self.launcher_btn)

        self.clear_btn = QPushButton("🗑️ Temizle")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self._clear_log)
        btn_layout.addWidget(self.clear_btn)
        
        self.cancel_btn = QPushButton("❌ İptal")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_action)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)
    
    def _apply_theme(self):
        """Tema uygula"""
        self.setStyleSheet("""
            QMainWindow {
                background: #1a202c;
            }
            QWidget {
                color: #e2e8f0;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #4a5568;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background: #2d3748;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #e2e8f0;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #4a5568;
                border-radius: 4px;
                background: #1a202c;
                color: #e2e8f0;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #4299e1;
            }
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                background: #4a5568;
                color: #e2e8f0;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5a6578;
            }
            QPushButton:pressed {
                background: #3a4558;
            }
            QPushButton:disabled {
                background: #2d3748;
                color: #718096;
            }
            QProgressBar {
                border: 1px solid #4a5568;
                border-radius: 4px;
                background: #1a202c;
                text-align: center;
                color: #e2e8f0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4299e1, stop:1 #48bb78);
                border-radius: 3px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #4a5568;
            }
            QCheckBox::indicator:checked {
                background: #4299e1;
                border-color: #4299e1;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #2d3748;
                border: 1px solid #4a5568;
                selection-background-color: #4299e1;
            }
        """)
    
    def _load_settings(self):
        """Ayarları yükle"""
        settings_file = Path.home() / ".nexor_build_manager.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                if settings.get('project_path'):
                    self.project_path_edit.setText(settings['project_path'])
                    self._load_current_version()  # Versiyonu yükle
                if settings.get('deploy_path'):
                    self.deploy_path_edit.setText(settings['deploy_path'])
                if settings.get('icon_path'):
                    self.icon_path_edit.setText(settings['icon_path'])
                if settings.get('build_mode_index') is not None:
                    self.build_mode_combo.setCurrentIndex(settings['build_mode_index'])
            except:
                pass
    
    def _save_settings(self):
        """Ayarları kaydet"""
        settings_file = Path.home() / ".nexor_build_manager.json"
        settings = {
            'project_path': self.project_path_edit.text(),
            'deploy_path': self.deploy_path_edit.text(),
            'icon_path': self.icon_path_edit.text(),
            'build_mode_index': self.build_mode_combo.currentIndex()
        }
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _browse_project(self):
        """Proje klasörü seç"""
        path = QFileDialog.getExistingDirectory(self, "Proje Klasörü Seçin")
        if path:
            self.project_path_edit.setText(path)
            self._load_current_version()
    
    def _load_current_version(self):
        """Mevcut versiyonu yükle"""
        project_path = self.project_path_edit.text()
        if not project_path:
            return
        
        version_file = Path(project_path) / "version.py"
        if not version_file.exists():
            self.current_version_label.setText("Bulunamadı")
            self.new_version_label.setText("--")
            return
        
        try:
            content = version_file.read_text(encoding='utf-8')
            match = re.search(r'VERSION\s*=\s*"([\d.]+)"', content)
            if match:
                version = match.group(1)
                self.current_version_label.setText(f"v{version}")
                self._update_version_preview()
            else:
                self.current_version_label.setText("Hata")
        except:
            self.current_version_label.setText("Hata")
    
    def _update_version_preview(self):
        """Yeni versiyon önizlemesi"""
        project_path = self.project_path_edit.text()
        if not project_path:
            self.new_version_label.setText("--")
            return
        
        version_file = Path(project_path) / "version.py"
        if not version_file.exists():
            self.new_version_label.setText("--")
            return
        
        try:
            content = version_file.read_text(encoding='utf-8')
            major = int(re.search(r'VERSION_MAJOR\s*=\s*(\d+)', content).group(1))
            minor = int(re.search(r'VERSION_MINOR\s*=\s*(\d+)', content).group(1))
            patch = int(re.search(r'VERSION_PATCH\s*=\s*(\d+)', content).group(1))
            
            bump_index = self.bump_type.currentIndex()
            
            if bump_index == 0:  # Yok
                self.new_version_label.setText(f"v{major}.{minor}.{patch}")
            elif bump_index == 1:  # Patch
                self.new_version_label.setText(f"v{major}.{minor}.{patch+1}")
            elif bump_index == 2:  # Minor
                self.new_version_label.setText(f"v{major}.{minor+1}.0")
            elif bump_index == 3:  # Major
                self.new_version_label.setText(f"v{major+1}.0.0")
        except:
            self.new_version_label.setText("Hata")
    
    def _browse_deploy(self):
        """Deploy hedefi seç"""
        path = QFileDialog.getExistingDirectory(self, "Deploy Hedefi Seçin")
        if path:
            self.deploy_path_edit.setText(path)
    
    def _browse_icon(self):
        """Icon dosyası seç"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Icon Dosyası Seçin", "", "Icon Files (*.ico)"
        )
        if path:
            self.icon_path_edit.setText(path)
    
    def _start_action(self, action: str):
        """Build/Deploy işlemini başlat"""
        project_path = self.project_path_edit.text()
        if not project_path or not Path(project_path).exists():
            QMessageBox.warning(self, "Hata", "Geçerli bir proje klasörü seçin!")
            return
        
        # Ayarları kaydet
        self._save_settings()
        
        # Config hazırla
        config = {
            'deploy_path': self.deploy_path_edit.text(),
            'icon_path': self.icon_path_edit.text(),
            'force_update': self.force_update_check.isChecked(),
            'changelog': self.changelog_edit.text(),
            'onefile': self.build_mode_combo.currentIndex() == 1,
            'slot_pattern': self.slot_pattern_check.isChecked(),
        }
        
        # Versiyon güncelleme tipi
        bump_index = self.bump_type.currentIndex()
        if bump_index > 0:
            config['bump_type'] = ['', 'patch', 'minor', 'major'][bump_index]
        
        # UI'ı güncelle
        self._clear_log()
        self.log(f"🚀 İşlem başlatılıyor: {action.upper()}", "cyan")
        self.log("="*50, "gray")
        
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Butonları devre dışı bırak
        self.build_btn.setEnabled(False)
        self.deploy_btn.setEnabled(False)
        self.build_deploy_btn.setEnabled(False)
        self.launcher_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        
        # Worker oluştur ve başlat
        try:
            self.worker = BuildWorker(project_path, action, config)
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self._on_finished)
            self.worker.start()
        except Exception as e:
            self.log(f"❌ Başlatma hatası: {e}", "red")
            self._on_finished(False, str(e))
    
    def _cancel_action(self):
        """İşlemi iptal et"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "İptal", "İşlemi iptal etmek istediğinizden emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.log("\n⚠️ İptal ediliyor...", "yellow")
                self.worker.cancel()
    
    def _on_finished(self, success: bool, message: str):
        """İşlem tamamlandı"""
        self.progress_bar.setVisible(False)
        
        # Butonları aktif et
        self.build_btn.setEnabled(True)
        self.deploy_btn.setEnabled(True)
        self.build_deploy_btn.setEnabled(True)
        self.launcher_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Başarılı", message)
        else:
            QMessageBox.critical(self, "Hata", message)
    
    def log(self, message: str, color: str = "white"):
        """Log mesajı ekle"""
        color_map = {
            'red': '#f56565',
            'green': '#48bb78',
            'yellow': '#ecc94b',
            'blue': '#4299e1',
            'cyan': '#00d4ff',
            'gray': '#a0aec0',
            'white': '#e2e8f0'
        }
        
        hex_color = color_map.get(color, color_map['white'])
        self.log_text.append(f'<span style="color: {hex_color};">{message}</span>')
        
        # Otomatik scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
    
    def _clear_log(self):
        """Log'u temizle"""
        self.log_text.clear()


# ============================================================
# MAIN
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BuildManagerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
