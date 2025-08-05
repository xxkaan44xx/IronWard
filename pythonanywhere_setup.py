#!/usr/bin/env python3
"""
PythonAnywhere Setup Script for Discord Bot
Bu dosya botunuzu PythonAnywhere'de 7/24 çalıştırmak için gerekli kurulum scriptini içerir.
"""

import os
import sys
import subprocess

def setup_pythonanywhere():
    """PythonAnywhere ortamını kurulum için hazırlar."""
    
    print("🚀 PythonAnywhere Discord Bot Kurulumu Başlatılıyor...")
    
    # 1. Gerekli paketleri yükle
    packages = [
        'discord.py==2.5.2',
        'aiohttp==3.12.15', 
        'python-dotenv==1.1.1'
    ]
    
    print("📦 Paketler yükleniyor...")
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', package], 
                         check=True, capture_output=True)
            print(f"✅ {package} yüklendi")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} yüklenemedi: {e}")
    
    # 2. Bot dosyalarını kontrol et
    required_files = [
        'main.py',
        'bot.py', 
        'database.py',
        'cogs/moderation.py',
        'cogs/utility.py',
        'cogs/settings.py',
        'utils/embeds.py',
        'utils/helpers.py',
        'languages/tr.json'
    ]
    
    print("\n📁 Dosyaları kontrol ediliyor...")
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Eksik dosyalar:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("✅ Tüm gerekli dosyalar mevcut")
    
    # 3. Environment dosyası oluştur
    env_content = """# Discord Bot Token - PythonAnywhere'de Environment Variables'a ekleyin
# DISCORD_BOT_TOKEN=your_bot_token_here

# Database Path
DATABASE_PATH=./moderation_bot.db

# Bot Configuration  
BOT_PREFIX=!
DEFAULT_LANGUAGE=tr
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ .env.example dosyası oluşturuldu")
    
    # 4. PythonAnywhere çalıştırma scripti oluştur
    pa_script = """#!/usr/bin/env python3
import os
import sys
import asyncio
from pathlib import Path

# Projenin ana dizinini Python path'ine ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Discord bot token'ı environment variable'dan al
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

if not DISCORD_TOKEN:
    print("❌ DISCORD_BOT_TOKEN environment variable bulunamadı!")
    print("PythonAnywhere Dashboard > Files > Environment variables bölümünden ekleyin")
    sys.exit(1)

# Bot'u başlat
if __name__ == "__main__":
    # main.py'deki main fonksiyonunu import et ve çalıştır
    try:
        from main import main
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Bot başlatılırken hata: {e}")
        import traceback
        traceback.print_exc()
"""
    
    with open('run_bot.py', 'w', encoding='utf-8') as f:
        f.write(pa_script)
    print("✅ run_bot.py dosyası oluşturuldu")
    
    # 5. Always On Task script oluştur
    always_on_script = """#!/usr/bin/env python3
import subprocess
import sys
import time
import os
from datetime import datetime

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def run_bot():
    \"\"\"Bot'u çalıştır ve hata durumunda yeniden başlat.\"\"\"
    while True:
        try:
            log_message("🤖 Bot başlatılıyor...")
            
            # Bot'u çalıştır
            result = subprocess.run([sys.executable, 'run_bot.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                log_message("✅ Bot normal şekilde kapandı")
            else:
                log_message(f"❌ Bot hata ile kapandı (kod: {result.returncode})")
                log_message(f"STDOUT: {result.stdout}")
                log_message(f"STDERR: {result.stderr}")
            
        except Exception as e:
            log_message(f"❌ Bot çalıştırılırken hata: {e}")
        
        # 30 saniye bekle ve tekrar başlat
        log_message("⏳ 30 saniye bekleniyor...")
        time.sleep(30)

if __name__ == "__main__":
    log_message("🚀 Always On Task başlatılıyor...")
    run_bot()
"""
    
    with open('always_on_task.py', 'w', encoding='utf-8') as f:
        f.write(always_on_script)
    print("✅ always_on_task.py dosyası oluşturuldu")
    
    print("\n🎉 PythonAnywhere kurulumu tamamlandı!")
    return True

if __name__ == "__main__":
    setup_pythonanywhere()