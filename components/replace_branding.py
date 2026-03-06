#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REDLINE NEXOR - Marka Değiştirme Scripti
Tüm REDLINE NEXOR referanslarını REDLINE NEXOR ile değiştirir
"""

import os
import sys
from pathlib import Path

def replace_branding(project_dir: Path):
    """
    Tüm Python dosyalarında REDLINE NEXOR -> REDLINE NEXOR değişikliği yap
    """
    print("🔄 Marka değiştirme başlıyor...")
    print(f"📁 Proje dizini: {project_dir}")
    print()
    
    replacements = {
        # Tam eşleşmeler
        "REDLINE NEXOR ERP": "REDLINE NEXOR ERP",
        "REDLINE NEXOR": "REDLINE NEXOR",
        "Redline Nexor ERP": "Redline Nexor ERP", 
        "Redline Nexor": "Redline Nexor",
        "Redline Nexor ERP": "Redline Nexor ERP",
        "Redline Nexor": "Redline Nexor",
        
        # Yorumlarda
        "REDLINE NEXOR - ": "REDLINE NEXOR - ",
        
        # Label'larda
        '"REDLINE NEXOR"': '"REDLINE NEXOR"',
        "'REDLINE NEXOR'": "'REDLINE NEXOR'",
        
        # Logo harfi (sidebar'da "A" yerine "R")
        'QLabel("R")': 'QLabel("R")',
    }
    
    fixed_files = []
    skipped_files = [
        "README",
        "CHANGELOG",
        ".git",
        "__pycache__",
        ".backup",
        ".old"
    ]
    
    # Tüm .py dosyalarını bul
    for py_file in project_dir.rglob("*.py"):
        # Atlanacak dosyaları kontrol et
        if any(skip in str(py_file) for skip in skipped_files):
            continue
        
        try:
            # Dosyayı oku
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Tüm değişiklikleri uygula
            for old, new in replacements.items():
                if old in content:
                    content = content.replace(old, new)
            
            # Değişiklik var mı kontrol et
            if content != original_content:
                # Yedek oluştur
                backup_file = py_file.with_suffix('.py.brandbak')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Değişiklikleri kaydet
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixed_files.append(py_file.relative_to(project_dir))
                print(f"  ✅ {py_file.name}")
        
        except Exception as e:
            print(f"  ⚠️  {py_file.name}: {e}")
    
    print()
    if fixed_files:
        print(f"✅ {len(fixed_files)} dosya güncellendi!")
        print("\nGüncellenen dosyalar:")
        for f in fixed_files:
            print(f"  - {f}")
    else:
        print("ℹ️  Güncellenecek dosya bulunamadı.")
    
    print()
    print("📝 Yapılan Değişiklikler:")
    print("  • 'REDLINE NEXOR' → 'REDLINE NEXOR'")
    print("  • Logo harfi 'A' → 'R'")
    print("  • Tüm dokümantasyon yorumları")
    
    print()
    print("💾 Yedekler:")
    print("  • Tüm dosyaların yedeği .brandbak uzantısıyla kaydedildi")
    print("  • Geri almak için: for f in *.brandbak; do mv $f ${f%.brandbak}; done")
    
    print()
    print("🔄 Uygulamayı yeniden başlatın:")
    print("   python main.py")


def main():
    print("""
╔═══════════════════════════════════════════════════╗
║        REDLINE NEXOR - MARKA DEĞİŞTİRME          ║
║     REDLINE NEXOR → REDLINE NEXOR (Global)          ║
╚═══════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    else:
        project_path = input("ERP proje yolunu girin: ").strip()
        project_path = project_path.strip('"').strip("'")
        project_dir = Path(project_path)
    
    if not project_dir.exists():
        print(f"❌ Dizin bulunamadı: {project_dir}")
        return 1
    
    # Onay al
    print(f"\n⚠️  UYARI: Bu işlem {project_dir} dizinindeki TÜM Python dosyalarını değiştirecek!")
    print("Devam etmek için 'evet' yazın: ", end='')
    confirm = input().strip().lower()
    
    if confirm not in ['evet', 'yes', 'e', 'y']:
        print("❌ İşlem iptal edildi.")
        return 0
    
    print()
    replace_branding(project_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
