
#!/usr/bin/env python3
"""
PythonAnywhere Runner for Discord Bot
Bu dosya botunuzu PythonAnywhere'de 7/24 çalıştırmak için kullanılır.
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_pythonanywhere.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('PythonAnywhereRunner')

def check_environment():
    """Environment ve dosyaları kontrol et."""
    logger.info("🔍 Environment kontrol ediliyor...")
    
    # Token kontrolü
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("❌ DISCORD_BOT_TOKEN environment variable bulunamadı!")
        logger.error("PythonAnywhere Dashboard > Account > Environment variables'dan ekleyin")
        return False
    
    if len(token) < 50:
        logger.error(f"❌ Token çok kısa! Uzunluk: {len(token)}")
        return False
    
    logger.info(f"✅ Token bulundu: {token[:5]}...{token[-5:]}")
    
    # Gerekli dosyaları kontrol et
    required_files = [
        'main.py',
        'bot.py',
        'database.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"❌ Gerekli dosya bulunamadı: {file}")
            return False
    
    logger.info("✅ Tüm gerekli dosyalar mevcut")
    return True

async def run_bot():
    """Bot'u çalıştır."""
    try:
        # Projenin ana dizinini Python path'ine ekle
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        logger.info("🤖 Discord botu başlatılıyor...")
        
        # main.py'den bot'u import et ve çalıştır
        from main import main
        await main()
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot manuel olarak durduruldu")
    except Exception as e:
        logger.error(f"❌ Bot çalıştırılırken hata: {e}")
        import traceback
        traceback.print_exc()
        raise

def main_runner():
    """Ana runner fonksiyonu."""
    logger.info("🚀 PythonAnywhere Discord Bot Runner başlatılıyor...")
    logger.info(f"📅 Başlatma zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Environment kontrolü
    if not check_environment():
        logger.error("❌ Environment kontrolleri başarısız!")
        sys.exit(1)
    
    # Bot'u çalıştır
    try:
        asyncio.run(run_bot())
    except Exception as e:
        logger.error(f"❌ Fatal hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_runner()
