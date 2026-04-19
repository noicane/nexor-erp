# -*- mode: python ; coding: utf-8 -*-
"""
NEXOR LAUNCHER - PyInstaller Spec
==================================
Slot pattern launcher icin tek dosyali, kucuk, hizli baslayan exe.
Sadece tkinter + stdlib kullanir.
"""

from pathlib import Path

ROOT_DIR = Path('.').absolute()
LAUNCHER_DIR = ROOT_DIR / 'launcher'

block_cipher = None

a = Analysis(
    [str(LAUNCHER_DIR / 'nexor_launcher.py')],
    pathex=[str(LAUNCHER_DIR)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Hicbiri lazim degil
        'PySide6', 'PyQt5', 'PyQt6',
        'numpy', 'pandas', 'matplotlib',
        'PIL', 'reportlab',
        'pyodbc', 'twilio', 'pywhatkit', 'pyautogui',
        'openpyxl', 'barcode',
        'unittest', 'test', 'tests',
        'IPython', 'notebook', 'sphinx',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NexorLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python3*.dll',
        'api-ms-win-*.dll',
        'ucrtbase.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT_DIR / 'assets' / 'icon.ico') if (ROOT_DIR / 'assets' / 'icon.ico').exists() else None,
    version_info=None,
)
