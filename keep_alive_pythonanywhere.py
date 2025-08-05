
#!/usr/bin/env python3
"""
PythonAnywhere Always On Task Runner
Bu dosya Always On Task'ta kullanılır ve bot'u sürekli çalışır tutar.
"""

import subprocess
import sys
import time
import os
import logging
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('always_on.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AlwaysOnTask')

class BotRunner:
    def __init__(self):
        self.restart_count = 0
        self.max_restarts = 50  # Maksimum restart sayısı
        self.restart_delay = 30  # Restart arası bekleme süresi (saniye)
        
    def log_system_info(self):
        """Sistem bilgilerini logla."""
        logger.info("📊 Sistem Bilgileri:")
        logger.info(f"Python sürümü: {sys.version}")
        logger.info(f"Çalışma dizini: {os.getcwd()}")
        logger.info(f"PID: {os.getpid()}")
        
    def check_bot_files(self):
        """Bot dosyalarının varlığını kontrol et."""
        required_files = ['run_pythonanywhere.py', 'main.py', 'bot.py']
        for file in required_files:
            if not os.path.exists(file):
                logger.error(f"❌ Gerekli dosya bulunamadı: {file}")
                return False
        return True
        
    def run_bot_process(self):
        """Bot sürecini çalıştır."""
        try:
            logger.info("🤖 Bot süreci başlatılıyor...")
            
            # Bot'u çalıştır
            process = subprocess.Popen(
                [sys.executable, 'run_pythonanywhere.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Process'i bekle
            stdout, stderr = process.communicate()
            
            # Sonuçları logla
            if process.returncode == 0:
                logger.info("✅ Bot normal şekilde kapandı")
            else:
                logger.error(f"❌ Bot hata ile kapandı (Return code: {process.returncode})")
                
            if stdout:
                logger.info(f"📤 STDOUT: {stdout[-500:]}")  # Son 500 karakter
                
            if stderr:
                logger.error(f"📤 STDERR: {stderr[-500:]}")  # Son 500 karakter
                
            return process.returncode
            
        except Exception as e:
            logger.error(f"❌ Bot süreci çalıştırılırken hata: {e}")
            return 1
    
    def should_restart(self, return_code):
        """Restart yapılıp yapılmayacağını belirle."""
        if self.restart_count >= self.max_restarts:
            logger.error(f"❌ Maksimum restart sayısına ulaşıldı ({self.max_restarts})")
            return False
            
        # Normal kapanma (KeyboardInterrupt) durumunda restart yapma
        if return_code == 0:
            logger.info("ℹ️ Bot normal şekilde kapandı, restart yapılmıyor")
            return False
            
        return True
    
    def run_forever(self):
        """Bot'u sürekli çalıştır."""
        logger.info("🚀 Always On Task başlatılıyor...")
        logger.info(f"📅 Başlatma zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.log_system_info()
        
        # Bot dosyalarını kontrol et
        if not self.check_bot_files():
            logger.error("❌ Gerekli dosyalar bulunamadı!")
            return
        
        while True:
            self.restart_count += 1
            logger.info(f"🔄 Bot başlatma denemesi #{self.restart_count}")
            
            # Environment değişkenini kontrol et
            if not os.environ.get('DISCORD_BOT_TOKEN'):
                logger.error("❌ DISCORD_BOT_TOKEN environment variable bulunamadı!")
                logger.error("PythonAnywhere Dashboard > Account > Environment variables'dan ekleyin")
                time.sleep(60)  # 1 dakika bekle
                continue
            
            # Bot'u çalıştır
            return_code = self.run_bot_process()
            
            # Restart gerekli mi?
            if not self.should_restart(return_code):
                break
                
            # Restart bekleme süresi
            logger.info(f"⏳ {self.restart_delay} saniye bekleniyor...")
            time.sleep(self.restart_delay)
        
        logger.info("🛑 Always On Task sonlandırılıyor...")

def main():
    """Ana fonksiyon."""
    runner = BotRunner()
    try:
        runner.run_forever()
    except KeyboardInterrupt:
        logger.info("⚠️ Manuel olarak durduruldu")
    except Exception as e:
        logger.error(f"❌ Fatal hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
