# -*- coding: utf-8 -*-
r"""
NEXOR LAUNCHER - Slot Pattern v1.0
====================================
Cevrimici/cevrimdisi calisma destegi olan launcher.

Akis:
    1. Sunucudan current.txt oku -> hedef versiyon
    2. Lokalde slot var mi? -> Direkt baslat
    3. Yoksa: robocopy ile tmp slota indir -> rename -> baslat
    4. Eski slot'lari temizle (son 3 versiyon kalir)

Sunucu Yapisi:
    \\AtlasNAS\Atmo_Logic\releases\
    +-- 4.4.0\
    |   +-- NexorERP.exe
    |   +-- _internal\
    |   +-- version.json
    +-- 4.4.1\
    +-- current.txt    (icerik: "4.4.1")

Client Yapisi:
    C:\Program Files\Nexor\NexorLauncher.exe   (Inno Setup, degismez)
    %LOCALAPPDATA%\Nexor\releases\
    +-- 4.4.0\   (eski slot - cevrimdisi fallback)
    +-- 4.4.1\   (aktif slot)

Cevrimdisi Modu:
    Sunucuya ulasilamazsa lokal'deki en yeni slot'u baslatir.
    Hicbir slot yoksa kullaniciya hata gosterir.
"""

import os
import sys
import re
import socket
import shutil
import subprocess
import threading
import queue
import logging
from pathlib import Path
from typing import Optional, List, Tuple

import tkinter as tk
from tkinter import ttk, messagebox

# =========================
# KONFIGURASYON
# =========================
APP_NAME = "Nexor"
APP_DISPLAY_NAME = "Nexor ERP"
EXE_NAME = "NexorERP.exe"
KEEP_SLOTS = 3  # Son 3 versiyon lokal'de tutulur

# Sunucu yolu - registry'den de okunabilir (Inno Setup veya kur.bat yazar)
# Default: AtlasNas hostname (ofis aginda calisir).
# VPN'de hostname cozulmuyorsa kur.bat veya Inno Setup ile registry override
# edilir: HKCU\Software\Nexor\ServerPath = \\192.168.10.35\atmo_logic\releases
DEFAULT_SERVER_PATH = r"\\AtlasNas\Atmo_Logic\releases"

# Lokal slot konumu
LOCAL_BASE = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / APP_NAME / "releases"

# Log dosyasi
LOG_DIR = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / APP_NAME / "logs"
LOG_FILE = LOG_DIR / "launcher.log"

# UI sabitleri
WINDOW_W, WINDOW_H = 460, 180
COLORS = {
    "bg": "#1a202c",
    "fg": "#e2e8f0",
    "muted": "#a0aec0",
    "accent": "#E2130D",  # Redline kirmizi
    "accent2": "#48bb78",
}

# Subprocess flag'i (konsol penceresi acmasin)
CREATE_NO_WINDOW = 0x08000000


# =========================
# LOGGER
# =========================
def setup_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8',
    )
    return logging.getLogger("launcher")


log = setup_logger()


# =========================
# SUNUCU PATH (registry destekli)
# =========================
def get_server_path() -> str:
    r"""
    Sunucu yolunu belirle. Oncelik:
        1. Registry: HKCU\Software\Nexor\ServerPath (Inno Setup yazar)
        2. Default: \\AtlasNAS\Atmo_Logic\releases
    """
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Nexor") as key:
            val, _ = winreg.QueryValueEx(key, "ServerPath")
            if val:
                log.info(f"Server path registry'den: {val}")
                return val
    except (FileNotFoundError, OSError, ImportError):
        pass
    log.info(f"Server path default: {DEFAULT_SERVER_PATH}")
    return DEFAULT_SERVER_PATH


# =========================
# VERSION HELPERS
# =========================
def parse_version(v: str) -> Optional[Tuple[int, ...]]:
    """4.4.1 -> (4, 4, 1). Hatali ise None."""
    try:
        return tuple(int(x) for x in v.strip().split('.'))
    except (ValueError, AttributeError):
        return None


def _server_host_from_path(server_path: str) -> Optional[str]:
    """\\AtlasNas\\Atmo_Logic\\releases -> 'AtlasNas'. Cozulemezse None."""
    m = re.match(r"^\\\\([^\\]+)\\", server_path)
    return m.group(1) if m else None


def probe_server(server_path: str, timeout: float = 2.0) -> bool:
    """
    SMB sunucuya hizli erisilebilirlik kontrolu (TCP 445).
    Default 30s SMB timeout yerine 2sn'de cevap alip donmemizi sagliyor.
    """
    host = _server_host_from_path(server_path)
    if not host:
        return True  # path acik UNC degilse skip et
    try:
        with socket.create_connection((host, 445), timeout=timeout):
            return True
    except (socket.timeout, OSError) as e:
        log.warning(f"SMB probe basarisiz ({host}:445): {e}")
        return False


def read_current_version(server_path: str) -> str:
    """Sunucudan current.txt oku. Hata firlatabilir."""
    cur_file = Path(server_path) / "current.txt"
    if not cur_file.exists():
        raise FileNotFoundError(f"current.txt bulunamadi: {cur_file}")
    version = cur_file.read_text(encoding='utf-8').strip()
    if not parse_version(version):
        raise ValueError(f"Gecersiz versiyon formati: {version!r}")
    return version


def slot_exe_path(version: str) -> Path:
    return LOCAL_BASE / version / EXE_NAME


def slot_exists(version: str) -> bool:
    return slot_exe_path(version).is_file()


def list_local_slots() -> List[Tuple[Tuple[int, ...], Path]]:
    """Lokal'deki tum slot'lari (versiyon tuple, path) olarak dondur. Yeniden eskiye sirali."""
    if not LOCAL_BASE.exists():
        return []
    slots = []
    for d in LOCAL_BASE.iterdir():
        if not d.is_dir() or d.name.endswith('.tmp'):
            continue
        v = parse_version(d.name)
        if v and (d / EXE_NAME).is_file():
            slots.append((v, d))
    return sorted(slots, reverse=True)


# =========================
# COPY (robocopy)
# =========================
def copy_slot(version: str, server_path: str, progress_q: queue.Queue, cancel_event: threading.Event):
    """
    Sunucudan version klasorunu indir. Progress'i kuyruga yazar.

    NOT: Daha once `rglob()` ile dosya sayimi yapiliyordu, fakat SMB share'de
    Python'un rglob cagrisi acilan handle'lari robocopy'nin source'u acmasini
    engelliyor (ERROR 267 - Dizin adi gecersiz). Bu yuzden count_files kaldirildi
    ve progress indeterminate moda alindi.

    Kuyruk mesajlari:
        ('progress', percent_int, status_str)  # pct=-1 -> indeterminate
        ('done', True, '')
        ('done', False, error_msg)
    """
    try:
        src = Path(server_path) / version
        dst_tmp = LOCAL_BASE / f"{version}.tmp"
        dst_final = LOCAL_BASE / version

        if not src.exists():
            progress_q.put(('done', False, f"Sunucuda versiyon bulunamadi:\n{src}"))
            return

        # Eski tmp varsa temizle
        if dst_tmp.exists():
            try:
                shutil.rmtree(dst_tmp)
            except Exception as e:
                log.warning(f"tmp temizleme uyarisi: {e}")

        LOCAL_BASE.mkdir(parents=True, exist_ok=True)

        cmd = [
            'robocopy',
            str(src),
            str(dst_tmp),
            '/E',          # alt klasorler dahil
            '/R:3',        # 3 retry
            '/W:2',        # 2 sn bekleme
            '/NDL',        # dizin listeleme yok
            '/NJH',        # job header yok
            '/NJS',        # job summary yok
            '/NP',         # dosya yuzdeleri yok
            '/COPY:DT',    # sadece Data + Timestamp (SMB'de Attribute yetkisi yok -> ERROR 267)
            '/DCOPY:T',    # dizin icin sadece Timestamp
        ]

        progress_q.put(('progress', -1, "Indiriliyor..."))

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='cp857',
            errors='ignore',
            creationflags=CREATE_NO_WINDOW,
        )

        copied = 0
        stdout_tail = []  # hata durumunda log'a yazmak icin son 20 satir
        for line in proc.stdout:
            if cancel_event.is_set():
                try:
                    proc.kill()
                except Exception:
                    pass
                # tmp temizle
                try:
                    shutil.rmtree(dst_tmp, ignore_errors=True)
                except Exception:
                    pass
                progress_q.put(('done', False, "Iptal edildi"))
                return

            line = line.strip()
            if not line:
                continue
            stdout_tail.append(line)
            if len(stdout_tail) > 20:
                stdout_tail.pop(0)
            copied += 1
            # Total bilinmiyor -> indeterminate; yalniz kopyalanan dosya sayisini goster
            progress_q.put(('progress', -1, f"Indiriliyor... ({copied} dosya)"))

        proc.wait()
        if proc.returncode >= 8:
            log.error(f"robocopy rc={proc.returncode} son satirlar:\n" + "\n".join(stdout_tail))
            progress_q.put(('done', False, f"Indirme hatasi (rc={proc.returncode}). Detay: logs/launcher.log"))
            return

        # Atomic rename: tmp -> final
        progress_q.put(('progress', 99, "Tamamlaniyor..."))
        if dst_final.exists():
            # Eski klasoru .old ile yeniden adlandir, sonra sil
            old = LOCAL_BASE / f"{version}.old"
            try:
                if old.exists():
                    shutil.rmtree(old, ignore_errors=True)
                dst_final.rename(old)
            except Exception:
                pass
            shutil.rmtree(old, ignore_errors=True)

        dst_tmp.rename(dst_final)
        log.info(f"Slot kuruldu: {version} ({copied} dosya)")
        progress_q.put(('progress', 100, f"Tamamlandi: {copied} dosya"))
        progress_q.put(('done', True, ''))

    except FileNotFoundError as e:
        log.error(f"robocopy bulunamadi: {e}")
        progress_q.put(('done', False, f"robocopy komutu bulunamadi: {e}"))
    except Exception as e:
        log.exception("copy_slot hatasi")
        progress_q.put(('done', False, f"Beklenmedik hata: {e}"))


# =========================
# CLEANUP
# =========================
def cleanup_old_slots(active_version: str, keep: int = KEEP_SLOTS):
    """
    Aktif versiyon dahil son `keep` slot'u tut, gerisini sil.
    .tmp klasorlerini ve eski .old'lari da siler.
    """
    if not LOCAL_BASE.exists():
        return

    # Tmp/old kalintilarini temizle
    for d in LOCAL_BASE.iterdir():
        if d.is_dir() and (d.name.endswith('.tmp') or d.name.endswith('.old')):
            shutil.rmtree(d, ignore_errors=True)

    slots = list_local_slots()  # Yeniden eskiye

    # Aktif versiyonu listenin basina al (varsa) - kesinlikle silinmesin
    av = parse_version(active_version)
    keep_set = set()
    if av:
        keep_set.add(av)

    # En yeni `keep` versiyonu sec
    for v, _ in slots[:keep]:
        keep_set.add(v)

    deleted = 0
    for v, path in slots:
        if v not in keep_set:
            try:
                shutil.rmtree(path)
                log.info(f"Eski slot silindi: {path.name}")
                deleted += 1
            except Exception as e:
                log.warning(f"Slot silme hatasi {path.name}: {e}")

    if deleted:
        log.info(f"Cleanup: {deleted} eski slot silindi")


# =========================
# LAUNCH
# =========================
def launch_app(version: str) -> bool:
    """Slot'taki exe'yi baslat. True/False."""
    exe = slot_exe_path(version)
    if not exe.is_file():
        log.error(f"Exe bulunamadi: {exe}")
        return False
    try:
        subprocess.Popen(
            [str(exe)],
            cwd=str(exe.parent),
            creationflags=CREATE_NO_WINDOW,
        )
        log.info(f"Baslatildi: {exe}")
        return True
    except Exception as e:
        log.exception("launch_app hatasi")
        messagebox.showerror(APP_DISPLAY_NAME, f"Uygulama baslatilamadi:\n{e}")
        return False


# =========================
# UI - PROGRESS DIALOG
# =========================
class ProgressDialog:
    def __init__(self, version: str, server_path: str):
        self.version = version
        self.server_path = server_path
        self.cancel_event = threading.Event()
        self.progress_q: queue.Queue = queue.Queue()
        self.success = False

        self.root = tk.Tk()
        self.root.title(APP_DISPLAY_NAME)
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Pencereyi ekran ortasina al
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = (sw - WINDOW_W) // 2
        y = (sh - WINDOW_H) // 2
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

        # Icon (varsa)
        try:
            ico = Path(sys.executable).parent / "icon.ico"
            if ico.exists():
                self.root.iconbitmap(str(ico))
        except Exception:
            pass

        # Frame
        frame = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=15)
        frame.pack(fill='both', expand=True)

        # Baslik
        title = tk.Label(
            frame,
            text=f"{APP_DISPLAY_NAME} v{version}",
            bg=COLORS["bg"], fg=COLORS["fg"],
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor='w')

        subtitle = tk.Label(
            frame,
            text="Yeni surum yukleniyor...",
            bg=COLORS["bg"], fg=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        subtitle.pack(anchor='w', pady=(2, 12))

        # Progress bar (ttk - tema lazim)
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure(
            "Nexor.Horizontal.TProgressbar",
            troughcolor=COLORS["bg"],
            background=COLORS["accent"],
            bordercolor=COLORS["bg"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
        )

        self.pbar = ttk.Progressbar(
            frame,
            style="Nexor.Horizontal.TProgressbar",
            orient='horizontal',
            length=WINDOW_W - 60,
            mode='determinate',
            maximum=100,
        )
        self.pbar.pack(fill='x')
        self._indeterminate = False

        # Status label
        self.status = tk.Label(
            frame,
            text="Hazirlaniyor...",
            bg=COLORS["bg"], fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor='w',
        )
        self.status.pack(fill='x', pady=(8, 0))

    def start(self):
        """Indirmeyi thread'de baslat ve UI'i poll et."""
        threading.Thread(
            target=copy_slot,
            args=(self.version, self.server_path, self.progress_q, self.cancel_event),
            daemon=True,
        ).start()
        self.root.after(100, self._poll_queue)
        self.root.mainloop()

    def _poll_queue(self):
        try:
            while True:
                msg = self.progress_q.get_nowait()
                kind = msg[0]
                if kind == 'progress':
                    _, pct, status = msg
                    if pct < 0:
                        # Indeterminate mode
                        if not self._indeterminate:
                            self.pbar.config(mode='indeterminate')
                            self.pbar.start(12)
                            self._indeterminate = True
                    else:
                        if self._indeterminate:
                            self.pbar.stop()
                            self.pbar.config(mode='determinate')
                            self._indeterminate = False
                        self.pbar['value'] = pct
                    self.status.config(text=status)
                elif kind == 'done':
                    _, ok, err = msg
                    self.success = ok
                    if ok:
                        self.root.after(300, self.root.destroy)
                    else:
                        self.status.config(text=f"Hata: {err}", fg="#fc8181")
                        self.root.after(2500, self.root.destroy)
                    return
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _on_close(self):
        # Kullanici X'e basti -> iptal
        self.cancel_event.set()
        self.status.config(text="Iptal ediliyor...", fg="#fc8181")
        self.root.after(1500, self.root.destroy)


# =========================
# OFFLINE DIALOG
# =========================
def show_offline_warning(latest_local: str) -> bool:
    """Sunucuya ulasilamadi - lokal versiyon ile devam edilsin mi?"""
    msg = (
        f"Sunucuya ulasilamiyor (VPN bagli mi?).\n\n"
        f"Lokal'deki son surum kullanilacak:\n"
        f"  • v{latest_local}\n\n"
        f"Devam etmek istiyor musunuz?"
    )
    return messagebox.askyesno(f"{APP_DISPLAY_NAME} - Cevrimdisi", msg, icon='warning')


def show_fatal_error(title: str, msg: str):
    messagebox.showerror(f"{APP_DISPLAY_NAME} - Hata", msg)


# =========================
# MAIN
# =========================
def main():
    log.info("=" * 60)
    log.info(f"Launcher basladi (PID {os.getpid()})")

    server_path = get_server_path()
    LOCAL_BASE.mkdir(parents=True, exist_ok=True)

    # 1. Sunucudan hedef versiyonu al (once hizli SMB probe)
    target_version: Optional[str] = None
    if probe_server(server_path, timeout=2.0):
        try:
            target_version = read_current_version(server_path)
            log.info(f"Sunucu hedef versiyon: {target_version}")
        except Exception as e:
            log.warning(f"current.txt okunamadi: {e}")
    else:
        log.warning(f"SMB probe basarisiz - offline moduna geciliyor: {server_path}")

    # 2. Sunucu erisilemiyor -> offline modu
    if target_version is None:
        slots = list_local_slots()
        if not slots:
            # Hicbir lokal slot yok -> kritik hata
            tk.Tk().withdraw()  # gizli root
            show_fatal_error(
                "Baglanti Hatasi",
                f"Sunucuya ulasilamiyor:\n{server_path}\n\n"
                f"Lokal'de yuklu hicbir surum yok.\n"
                f"VPN bagli oldugundan emin olun ve tekrar deneyin."
            )
            log.error("Sunucu yok + lokal slot yok -> exit")
            sys.exit(2)

        # Lokal'de slot var -> kullaniciya sor
        latest_local = ".".join(str(x) for x in slots[0][0])
        tk.Tk().withdraw()
        if not show_offline_warning(latest_local):
            log.info("Kullanici offline modu reddetti -> exit")
            sys.exit(0)
        target_version = latest_local

    # 3. Hedef slot lokal'de var mi?
    if slot_exists(target_version):
        log.info(f"Slot lokal: {target_version} -> direkt baslat")
        if launch_app(target_version):
            cleanup_old_slots(target_version)
            sys.exit(0)
        else:
            sys.exit(3)

    # 4. Slot yok -> indir
    log.info(f"Slot yok, indirme baslayacak: {target_version}")
    dialog = ProgressDialog(target_version, server_path)
    dialog.start()

    if not dialog.success:
        log.error(f"Indirme basarisiz: {target_version}")
        # Lokal'de eski bir slot varsa ona dus
        slots = list_local_slots()
        if slots:
            latest_local = ".".join(str(x) for x in slots[0][0])
            tk.Tk().withdraw()
            if messagebox.askyesno(
                APP_DISPLAY_NAME,
                f"Yeni surum indirilemedi.\n\n"
                f"Lokal'deki v{latest_local} ile devam edilsin mi?"
            ):
                if launch_app(latest_local):
                    sys.exit(0)
        sys.exit(4)

    # 5. Indirme basarili -> baslat + cleanup
    if launch_app(target_version):
        cleanup_old_slots(target_version)
        sys.exit(0)
    sys.exit(5)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Launcher fatal hatasi")
        try:
            tk.Tk().withdraw()
            show_fatal_error("Beklenmedik Hata",
                             f"Launcher beklenmedik bir hatayla karsilasti.\n\n"
                             f"Detaylar log dosyasinda:\n{LOG_FILE}")
        except Exception:
            pass
        sys.exit(99)
