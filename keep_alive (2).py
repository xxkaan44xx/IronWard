"""
Render deployment service - combines Discord bot with web server
"""
import os
import threading
import time
import asyncio
from flask import Flask, jsonify

# Flask web servisi
app = Flask(__name__)

# Bot durumu için global değişken
bot_status = "Starting..."
bot_error = None

@app.route('/')
def home():
    return f'''
    <html>
    <head><title>IronWard Discord Bot</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px; background: #2c3e50; color: white;">
        <h1>🛡️ IronWard Discord Bot</h1>
        <p>Bot durumu: <span style="color: {'#2ecc71' if 'Aktif' in bot_status else '#e74c3c'};">{bot_status}</span></p>
        <p>Bu sayfa Render servisini aktif tutar ve bot durumunu gösterir.</p>
        {f'<p style="color: #e74c3c;">Hata: {bot_error}</p>' if bot_error else ''}
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'ironward-bot',
        'bot_status': bot_status,
        'error': bot_error
    })

@app.route('/ping')
def ping():
    return jsonify({'response': 'pong'})

def start_discord_bot():
    """Discord botunu ayrı thread'de başlat"""
    global bot_status, bot_error
    try:
        # Discord bot import ve çalıştırma
        bot_status = "Bağlanıyor..."
        
        # Discord bot token kontrolü
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            bot_error = "DISCORD_BOT_TOKEN environment variable bulunamadı!"
            bot_status = "Token Hatası"
            return
            
        # Bot import
        import discord
        from discord.ext import commands
        
        bot_status = "Discord'a bağlanıyor..."
        
        # Basit bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            global bot_status
            bot_status = f"Aktif - {len(bot.guilds)} sunucuda"
            print(f"✅ Bot aktif: {bot.user.name if bot.user else 'Unknown'} - {len(bot.guilds)} sunucuda")
        
        @bot.event
        async def on_connect():
            global bot_status
            bot_status = "Discord'a bağlandı"
            print("🔗 Discord'a bağlandı")
            
        # Bot'u çalıştır
        bot.run(token)
        
    except Exception as e:
        bot_error = str(e)
        bot_status = "Hata"
        print(f"❌ Bot hatası: {e}")

def start_web_server():
    """Web serverini başlat"""
    # Render dinamik port kullanır, default 10000
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Web server başlatılıyor - Port: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # Discord botunu ayrı thread'de başlat
    bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
    bot_thread.start()
    
    # Web server'ı ana thread'de çalıştır (Render için gerekli)
    start_web_server()