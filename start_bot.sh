
#!/bin/bash

# PythonAnywhere Discord Bot Başlatma Scripti

echo "🚀 Discord Bot başlatılıyor..."

# Python versiyonunu kontrol et
echo "🐍 Python versiyonu:"
python3 --version

# Token kontrolü
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "❌ DISCORD_BOT_TOKEN environment variable bulunamadı!"
    echo "PythonAnywhere Dashboard > Account > Environment variables'dan ekleyin"
    exit 1
fi

echo "✅ Token bulundu"

# Gerekli paketleri kontrol et ve yükle
echo "📦 Paketler kontrol ediliyor..."
pip3 install --user discord.py==2.5.2 aiohttp==3.12.15 python-dotenv==1.1.1

# Bot'u başlat
echo "🤖 Bot başlatılıyor..."
python3 run_pythonanywhere.py
