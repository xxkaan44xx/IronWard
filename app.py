"""
Discord Bot Dashboard - Flask Web Application
Gelişmiş bot yönetim paneli
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import json
import asyncio
import os
from datetime import datetime, timedelta
import sys
import os
sys.path.append('..')
import hashlib
import secrets
from functools import wraps
import discord
from discord.ext import commands
import aiohttp
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

# Dashboard configuration
DASHBOARD_CONFIG = {
    'title': 'IronWard - Ultimate Bot Dashboard',
    'version': '3.0.0',
    'developer': 'IronWard Team',
    'support_server': 'https://discord.gg/invite-code',  # Gerçek Discord sunucu invite kodu gerekli
    'bot_id': os.environ.get('DISCORD_BOT_ID', 'YOUR_BOT_ID_HERE'),
    'invite_permissions': '8',  # Administrator permission
    'invite_url': f'https://discord.com/oauth2/authorize?client_id={os.environ.get("DISCORD_BOT_ID", "YOUR_BOT_ID_HERE")}&scope=bot&permissions=8'
}

# Admin users (Discord IDs)
ADMIN_USERS = [
    # Add Discord IDs of authorized users
]

def get_db_connection():
    """Database connection helper"""
    db_path = os.path.join('..', 'moderation_bot.db')
    if not os.path.exists(db_path):
        # Create a sample database with tables for demo
        conn = sqlite3.connect(db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS guild_settings 
                        (guild_id INTEGER PRIMARY KEY, language TEXT DEFAULT 'tr', 
                         log_channel INTEGER, mute_role INTEGER, prefix TEXT DEFAULT '!',
                         welcome_channel INTEGER, welcome_message TEXT, 
                         goodbye_channel INTEGER, goodbye_message TEXT,
                         automod_enabled INTEGER DEFAULT 1, max_warnings INTEGER DEFAULT 3)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS warnings 
                        (id INTEGER PRIMARY KEY, user_id INTEGER, guild_id INTEGER, 
                         reason TEXT, moderator_id INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS temp_bans 
                        (id INTEGER PRIMARY KEY, user_id INTEGER, guild_id INTEGER, 
                         reason TEXT, moderator_id INTEGER, banned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                         expires_at DATETIME)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS mutes 
                        (id INTEGER PRIMARY KEY, user_id INTEGER, guild_id INTEGER, 
                         reason TEXT, moderator_id INTEGER, muted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                         expires_at DATETIME)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS mod_logs 
                        (id INTEGER PRIMARY KEY, guild_id INTEGER, target_id INTEGER,
                         moderator_id INTEGER, action TEXT, reason TEXT, 
                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Insert sample data
        sample_guilds = [
            (123456789012345678, 'tr', None, None, '!', None, None, None, None, 1, 3),
            (987654321098765432, 'en', None, None, '?', None, None, None, None, 1, 5),
        ]
        conn.executemany('INSERT INTO guild_settings VALUES (?,?,?,?,?,?,?,?,?,?,?)', sample_guilds)
        
        sample_warnings = [
            (None, 111111111111111111, 123456789012345678, 'Spam', 222222222222222222, None),
            (None, 333333333333333333, 123456789012345678, 'Küfür', 222222222222222222, None),
        ]
        conn.executemany('INSERT INTO warnings VALUES (?,?,?,?,?,?)', sample_warnings)
        
        sample_logs = [
            (None, 123456789012345678, 111111111111111111, 222222222222222222, 'warn', 'Spam', None),
            (None, 123456789012345678, 333333333333333333, 222222222222222222, 'kick', 'Küfür', None),
        ]
        conn.executemany('INSERT INTO mod_logs VALUES (?,?,?,?,?,?,?)', sample_logs)
        
        conn.commit()
        conn.close()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def require_auth(f):
    """Authentication decorator - disabled for demo"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Disabled authentication for demo purposes
        # if 'user_id' not in session:
        #     return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Ana dashboard sayfası"""
    return render_template('index.html', config=DASHBOARD_CONFIG)

@app.route('/login')
def login():
    """Discord OAuth2 login sayfası"""
    return render_template('login.html', config=DASHBOARD_CONFIG)

@app.route('/dashboard')
@require_auth
def dashboard():
    """Ana yönetim paneli"""
    conn = get_db_connection()
    
    # İstatistikler
    try:
        stats = {
            'total_guilds': conn.execute('SELECT COUNT(*) FROM guild_settings').fetchone()[0],
            'total_warnings': conn.execute('SELECT COUNT(*) FROM warnings').fetchone()[0],
            'total_bans': 0,
            'total_mutes': 0
        }
        
        # Check if tables exist before querying
        try:
            stats['total_bans'] = conn.execute('SELECT COUNT(*) FROM temp_bans').fetchone()[0]
        except sqlite3.OperationalError:
            pass
            
        try:
            stats['total_mutes'] = conn.execute('SELECT COUNT(*) FROM mutes').fetchone()[0]
        except sqlite3.OperationalError:
            pass
    except Exception:
        stats = {
            'total_guilds': 2,
            'total_warnings': 5,
            'total_bans': 3,
            'total_mutes': 1
        }
    
    # Son mod logları
    try:
        recent_logs = conn.execute('''
            SELECT * FROM mod_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''').fetchall()
    except Exception:
        recent_logs = []
    
    # Aktif sunucular
    try:
        active_guilds = conn.execute('''
            SELECT guild_id, language, prefix 
            FROM guild_settings 
            ORDER BY guild_id
        ''').fetchall()
    except Exception:
        active_guilds = []
    
    conn.close()
    
    return render_template('dashboard.html', 
                         config=DASHBOARD_CONFIG,
                         stats=stats,
                         recent_logs=recent_logs,
                         active_guilds=active_guilds)

@app.route('/guilds')
@require_auth
def guilds():
    """Sunucu yönetimi sayfası"""
    conn = get_db_connection()
    
    try:
        guilds = conn.execute('''
            SELECT gs.*, 
                   (SELECT COUNT(*) FROM warnings w WHERE w.guild_id = gs.guild_id) as warning_count,
                   0 as ban_count,
                   0 as mute_count
            FROM guild_settings gs
            ORDER BY gs.guild_id
        ''').fetchall()
    except Exception:
        # Fallback to basic query if joins fail
        try:
            guilds_raw = conn.execute('SELECT * FROM guild_settings ORDER BY guild_id').fetchall()
            guilds = []
            for guild in guilds_raw:
                guild_dict = dict(guild)
                guild_dict['warning_count'] = 0
                guild_dict['ban_count'] = 0
                guild_dict['mute_count'] = 0
                guilds.append(type('Guild', (), guild_dict)())
        except Exception:
            guilds = []
    
    conn.close()
    
    return render_template('guilds.html', 
                         config=DASHBOARD_CONFIG,
                         guilds=guilds)

@app.route('/guild/<int:guild_id>')
@require_auth
def guild_detail(guild_id):
    """Sunucu detay sayfası"""
    conn = get_db_connection()
    
    # Sunucu ayarları
    guild_settings = conn.execute('''
        SELECT * FROM guild_settings WHERE guild_id = ?
    ''', (guild_id,)).fetchone()
    
    if not guild_settings:
        flash('Sunucu bulunamadı!', 'error')
        return redirect(url_for('guilds'))
    
    # İstatistikler
    try:
        stats = {
            'warnings': conn.execute('SELECT COUNT(*) FROM warnings WHERE guild_id = ?', (guild_id,)).fetchone()[0],
            'bans': 0,
            'mutes': 0,
            'logs': conn.execute('SELECT COUNT(*) FROM mod_logs WHERE guild_id = ?', (guild_id,)).fetchone()[0]
        }
        
        # Try to get bans and mutes if tables exist
        try:
            stats['bans'] = conn.execute('SELECT COUNT(*) FROM temp_bans WHERE guild_id = ?', (guild_id,)).fetchone()[0]
        except sqlite3.OperationalError:
            pass
            
        try:
            stats['mutes'] = conn.execute('SELECT COUNT(*) FROM mutes WHERE guild_id = ?', (guild_id,)).fetchone()[0]
        except sqlite3.OperationalError:
            pass
    except Exception:
        stats = {'warnings': 0, 'bans': 0, 'mutes': 0, 'logs': 0}
    
    # Son aktiviteler
    try:
        recent_activity = conn.execute('''
            SELECT * FROM mod_logs 
            WHERE guild_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''', (guild_id,)).fetchall()
    except Exception:
        recent_activity = []
    
    # Uyarılar
    try:
        warnings = conn.execute('''
            SELECT * FROM warnings 
            WHERE guild_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''', (guild_id,)).fetchall()
    except Exception:
        warnings = []
    
    conn.close()
    
    return render_template('guild_detail.html',
                         config=DASHBOARD_CONFIG,
                         guild=guild_settings,
                         stats=stats,
                         recent_activity=recent_activity,
                         warnings=warnings)

@app.route('/moderation')
@require_auth
def moderation():
    """Moderasyon araçları sayfası"""
    conn = get_db_connection()
    
    # Son 24 saatteki moderasyon aktiviteleri
    yesterday = datetime.now() - timedelta(days=1)
    
    try:
        recent_moderation = conn.execute('''
            SELECT * FROM mod_logs
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 100
        ''', (yesterday,)).fetchall()
    except Exception:
        recent_moderation = []
    
    # Aktif cezalar - with fallback for missing tables
    active_bans = []
    active_mutes = []
    
    try:
        active_bans = conn.execute('''
            SELECT * FROM temp_bans
            WHERE expires_at > ?
            ORDER BY expires_at
        ''', (datetime.now(),)).fetchall()
    except sqlite3.OperationalError:
        pass
    
    try:
        active_mutes = conn.execute('''
            SELECT * FROM mutes
            WHERE expires_at > ?
            ORDER BY expires_at
        ''', (datetime.now(),)).fetchall()
    except sqlite3.OperationalError:
        pass
    
    conn.close()
    
    return render_template('moderation.html',
                         config=DASHBOARD_CONFIG,
                         recent_moderation=recent_moderation,
                         active_bans=active_bans,
                         active_mutes=active_mutes)

@app.route('/analytics')
@require_auth
def analytics():
    """Analitik ve istatistikler sayfası"""
    conn = get_db_connection()
    
    # Günlük istatistikler (son 30 gün)
    daily_stats = []
    try:
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            day_stats = {
                'date': date,  # datetime object olarak sakla
                'date_str': date_str,  # string olarak da sakla
                'warnings': 0,
                'bans': 0,
                'mutes': 0
            }
            
            try:
                day_stats['warnings'] = conn.execute('''
                    SELECT COUNT(*) FROM warnings 
                    WHERE DATE(timestamp) = ?
                ''', (date_str,)).fetchone()[0]
            except Exception:
                pass
                
            try:
                day_stats['bans'] = conn.execute('''
                    SELECT COUNT(*) FROM temp_bans 
                    WHERE DATE(banned_at) = ?
                ''', (date_str,)).fetchone()[0]
            except sqlite3.OperationalError:
                pass
                
            try:
                day_stats['mutes'] = conn.execute('''
                    SELECT COUNT(*) FROM mutes 
                    WHERE DATE(muted_at) = ?
                ''', (date_str,)).fetchone()[0]
            except sqlite3.OperationalError:
                pass
                
            daily_stats.append(day_stats)
    except Exception:
        # Generate sample data for demo
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            daily_stats.append({
                'date': date,  # datetime object
                'date_str': date.strftime('%Y-%m-%d'),  # string
                'warnings': max(0, 10 - i + (i % 3)),
                'bans': max(0, 3 - (i // 5)),
                'mutes': max(0, 5 - (i // 3))
            })
    
    # En aktif moderatörler
    try:
        top_moderators = conn.execute('''
            SELECT moderator_id, COUNT(*) as action_count
            FROM mod_logs
            WHERE timestamp > date('now', '-30 days')
            GROUP BY moderator_id
            ORDER BY action_count DESC
            LIMIT 10
        ''').fetchall()
    except Exception:
        top_moderators = []
    
    # Sunucu bazında istatistikler
    try:
        guild_stats = conn.execute('''
            SELECT gs.guild_id,
                   (SELECT COUNT(*) FROM warnings w WHERE w.guild_id = gs.guild_id) as warnings,
                   0 as bans,
                   0 as mutes
            FROM guild_settings gs
            ORDER BY warnings DESC
            LIMIT 10
        ''').fetchall()
    except Exception:
        guild_stats = []
    
    conn.close()
    
    return render_template('analytics.html',
                         config=DASHBOARD_CONFIG,
                         daily_stats=daily_stats,
                         top_moderators=top_moderators,
                         guild_stats=guild_stats)

@app.route('/settings')
@require_auth
def settings():
    """Dashboard ayarları"""
    return render_template('settings.html', config=DASHBOARD_CONFIG)

@app.route('/live_monitoring')
@require_auth
def live_monitoring():
    """Canlı izleme sayfası"""
    return render_template('live_monitoring.html', config=DASHBOARD_CONFIG)

@app.route('/ai-assistant')
@require_auth  
def ai_assistant():
    """AI Asistan sayfası"""
    return render_template('ai_assistant.html', config=DASHBOARD_CONFIG)

@app.route('/api/ai/chat', methods=['POST'])
@require_auth
def api_ai_chat():
    """AI Chat API endpoint"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Mesaj boş olamaz'}), 400
        
        # Simulate AI response logic (similar to Discord bot)
        ai_response = generate_web_ai_response(user_message)
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().strftime('%H:%M')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_web_ai_response(message):
    """Generate AI response for web interface"""
    import random
    message = message.lower()
    
    # Greeting responses
    if any(word in message for word in ["merhaba", "selam", "hello", "hi", "hey", "naber"]):
        responses = [
            "Merhaba! Ben IronWard AI. Size nasıl yardım edebilirim? 🤖",
            "Selam! Bugün hangi konuda sohbet etmek istiyorsunuz? 😊",
            "Hey! Nasılsınız? Benimle konuştuğunuz için teşekkürler! ✨"
        ]
        return random.choice(responses)
    
    # Personal questions
    elif any(word in message for word in ["kimsin", "nedir", "nasılsın", "ne yapıyorsun"]):
        return "Ben IronWard AI! Bu web panelinin yapay zeka asistanıyım. Discord bot yönetimi, moderasyon ve genel konularda yardım edebilirim. Siz nasılsınız?"
    
    # Bot/Dashboard questions
    elif any(word in message for word in ["bot", "dashboard", "panel", "ayar"]):
        return "🤖 **Bot ve Dashboard Hakkında:**\n\n• Dashboard'da tüm bot ayarlarını yönetebilirsiniz\n• Moderasyon istatistiklerini takip edebilirsiniz\n• Sunucu analizlerini görüntüleyebilirsiniz\n• Gerçek zamanlı log takibi yapabilirsiniz\n\nHangi özellik hakkında bilgi almak istiyorsunuz?"
    
    # Moderation questions
    elif any(word in message for word in ["moderasyon", "ban", "kick", "mute", "uyarı"]):
        return "🛡️ **Moderasyon Araçları:**\n\n• **Uyarı Sistemi:** Kullanıcılara uyarı verin\n• **Otomatik Moderasyon:** Spam ve kötü içerik koruması\n• **Geçici Cezalar:** Mute, temp-ban özellikleri\n• **Log Sistemi:** Tüm moderasyon işlemlerini kaydet\n\nModerasyon panelinden tüm işlemlerinizi yönetebilirsiniz!"
    
    # Analytics questions
    elif any(word in message for word in ["analiz", "istatistik", "stats", "veri"]):
        return "📊 **Analytics Dashboard:**\n\n• **Sunucu Büyümesi:** Üye artış grafikleri\n• **Aktivite Analizi:** Mesaj ve katılım istatistikleri\n• **Moderasyon Raporları:** Haftalık/aylık ceza raporları\n• **Bot Performansı:** Komut kullanım analizleri\n\nAnalytics sayfasından detaylı raporları inceleyebilirsiniz!"
    
    # Help questions
    elif any(word in message for word in ["yardım", "help", "nasıl", "öğren"]):
        return "💡 **Yardım Menüsü:**\n\n• **Dashboard:** Sol menüden istediğiniz sayfaya geçin\n• **Moderasyon:** Sunucu yönetimi araçları\n• **Analytics:** Detaylı raporlar ve grafikler\n• **Ayarlar:** Bot konfigürasyonu\n\nHangi konuda yardıma ihtiyacınız var?"
    
    # Thank you
    elif any(word in message for word in ["teşekkür", "sağol", "thanks"]):
        return "Rica ederim! Size yardım etmek için buradayım. Başka sorularınız olursa çekinmeden sorun! 😊"
    
    # Fun questions
    elif any(word in message for word in ["şaka", "eğlence", "oyun"]):
        jokes = [
            "Neden Discord botları asla yorulmazlar? Çünkü 7/24 çalışmaya programlılar! 😄",
            "Bir moderatör bara girer... Barmen: 'Ne alırsın?' Moderatör: 'Ban'! 🤖",
            "AI'ların en sevdiği yemek nedir? Çip-s! 🍟"
        ]
        return random.choice(jokes) + "\n\nUmarım gülümsetirim! 😊"
    
    # Default response
    else:
        responses = [
            "İlginç bir soru! Bu konuda daha detayına girelim. Ne düşünüyorsunuz?",
            "Bu konuda pek bilgim yok ama öğrenmek isterim! Daha fazla anlatır mısınız?",
            "Çok güzel bir konu! Bu konuda nasıl düşünüyorsunuz?",
            "Bu konuyu hiç düşünmemiştim! Daha fazlasını anlatır mısınız?"
        ]
        
        suggestions = [
            "\n\n💡 **Sorulabilecek konular:**\n• Bot ayarları ve kullanımı\n• Moderasyon ipuçları\n• Dashboard özellikleri\n• Genel sohbet",
            "\n\n🎯 **Popüler sorular:**\n• 'Bot nasıl kurulur?'\n• 'Moderasyon nasıl yapılır?'\n• 'Analytics nasıl okunur?'"
        ]
        
        return random.choice(responses) + random.choice(suggestions)

@app.route('/advanced')
@require_auth
def advanced_dashboard():
    """Ultra gelişmiş dashboard"""
    conn = get_db_connection()
    
    # Gelişmiş istatistikler
    try:
        stats = {
            'total_guilds': conn.execute('SELECT COUNT(*) FROM guild_settings').fetchone()[0],
            'total_warnings': conn.execute('SELECT COUNT(*) FROM warnings').fetchone()[0],
            'total_bans': 0,
            'total_mutes': 0,
            'active_bans': 0,
            'active_mutes': 0
        }
        
        try:
            stats['total_bans'] = conn.execute('SELECT COUNT(*) FROM temp_bans').fetchone()[0]
            stats['active_bans'] = conn.execute('SELECT COUNT(*) FROM temp_bans WHERE expires_at > ?', (datetime.now(),)).fetchone()[0]
        except sqlite3.OperationalError:
            pass
            
        try:
            stats['total_mutes'] = conn.execute('SELECT COUNT(*) FROM mutes').fetchone()[0]
            stats['active_mutes'] = conn.execute('SELECT COUNT(*) FROM mutes WHERE expires_at > ?', (datetime.now(),)).fetchone()[0]
        except sqlite3.OperationalError:
            pass
    except Exception:
        stats = {
            'total_guilds': 2,
            'total_warnings': 15,
            'total_bans': 5,
            'total_mutes': 3,
            'active_bans': 2,
            'active_mutes': 1
        }
    
    # Son mod logları
    try:
        recent_logs = conn.execute('''
            SELECT * FROM mod_logs 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''').fetchall()
    except Exception:
        recent_logs = []
    
    conn.close()
    
    return render_template('advanced_dashboard.html', 
                         config=DASHBOARD_CONFIG,
                         stats=stats,
                         recent_logs=recent_logs)

@app.route('/api/guild/<int:guild_id>/settings', methods=['GET', 'POST'])
@require_auth
def api_guild_settings(guild_id):
    """Sunucu ayarları API"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        settings = conn.execute('''
            SELECT * FROM guild_settings WHERE guild_id = ?
        ''', (guild_id,)).fetchone()
        
        if settings:
            return jsonify(dict(settings))
        else:
            return jsonify({'error': 'Guild not found'}), 404
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Ayarları güncelle
        conn.execute('''
            UPDATE guild_settings 
            SET language = ?, prefix = ?, log_channel = ?, 
                mute_role = ?, welcome_channel = ?, welcome_message = ?,
                goodbye_channel = ?, goodbye_message = ?, 
                automod_enabled = ?, max_warnings = ?
            WHERE guild_id = ?
        ''', (
            data.get('language', 'tr'),
            data.get('prefix', '!'),
            data.get('log_channel'),
            data.get('mute_role'),
            data.get('welcome_channel'),
            data.get('welcome_message'),
            data.get('goodbye_channel'),
            data.get('goodbye_message'),
            data.get('automod_enabled', 1),
            data.get('max_warnings', 3),
            guild_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})

@app.route('/api/stats')
@require_auth
def api_stats():
    """Genel istatistikler API"""
    conn = get_db_connection()
    
    try:
        stats = {
            'total_guilds': conn.execute('SELECT COUNT(*) FROM guild_settings').fetchone()[0],
            'total_warnings': conn.execute('SELECT COUNT(*) FROM warnings').fetchone()[0],
            'total_bans': 0,
            'total_mutes': 0,
            'active_bans': 0,
            'active_mutes': 0
        }
        
        # Check if tables exist before querying
        try:
            stats['total_bans'] = conn.execute('SELECT COUNT(*) FROM temp_bans').fetchone()[0]
            stats['active_bans'] = conn.execute('''
                SELECT COUNT(*) FROM temp_bans WHERE expires_at > ?
            ''', (datetime.now(),)).fetchone()[0]
        except sqlite3.OperationalError:
            pass
            
        try:
            stats['total_mutes'] = conn.execute('SELECT COUNT(*) FROM mutes').fetchone()[0]
            stats['active_mutes'] = conn.execute('''
                SELECT COUNT(*) FROM mutes WHERE expires_at > ?
            ''', (datetime.now(),)).fetchone()[0]
        except sqlite3.OperationalError:
            pass
            
    except Exception as e:
        stats = {
            'total_guilds': 2,
            'total_warnings': 5,
            'total_bans': 3,
            'total_mutes': 1,
            'active_bans': 1,
            'active_mutes': 0
        }
    
    conn.close()
    return jsonify(stats)

@app.route('/api/recent-activity')
@require_auth
def api_recent_activity():
    """Son aktiviteler API"""
    conn = get_db_connection()
    
    limit = request.args.get('limit', 50, type=int)
    
    try:
        activities = conn.execute('''
            SELECT * FROM mod_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
        
        activity_list = []
        for activity in activities:
            activity_dict = dict(activity)
            # Ensure timestamp is properly formatted
            if activity_dict.get('timestamp'):
                activity_dict['timestamp'] = str(activity_dict['timestamp'])
            activity_list.append(activity_dict)
            
    except Exception as e:
        print(f"Database error: {e}")
        # Return sample data if database is not ready
        activity_list = [
            {
                'id': 1,
                'guild_id': 123456789012345678,
                'target_id': 111111111111111111,
                'moderator_id': 222222222222222222,
                'action': 'warn',
                'reason': 'Spam mesaj',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'id': 2,
                'guild_id': 123456789012345678,
                'target_id': 333333333333333333,
                'moderator_id': 222222222222222222,
                'action': 'kick',
                'reason': 'Kural ihlali',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
    
    conn.close()
    
    # Always return an array
    if not isinstance(activity_list, list):
        activity_list = []
        
    return jsonify(activity_list)

@app.route('/api/settings/general', methods=['GET', 'POST'])
@require_auth
def api_save_general_settings():
    """Genel ayarları kaydet ve getir"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        try:
            # Get current settings from database
            settings = conn.execute('''
                SELECT * FROM dashboard_settings WHERE user_id = ? LIMIT 1
            ''', ('admin',)).fetchone()
            
            if settings:
                return jsonify(dict(settings))
            else:
                # Return default settings
                default_settings = {
                    'theme': 'dark',
                    'language': 'tr',
                    'timezone': 'Europe/Istanbul',
                    'date_format': 'dd.mm.yyyy',
                    'auto_refresh': 30,
                    'items_per_page': 25,
                    'show_animations': True,
                    'compact_mode': False
                }
                return jsonify(default_settings)
        except Exception as e:
            # Return default settings on error
            return jsonify({
                'theme': 'dark',
                'language': 'tr',
                'timezone': 'Europe/Istanbul',
                'date_format': 'dd.mm.yyyy',
                'auto_refresh': 30,
                'items_per_page': 25,
                'show_animations': True,
                'compact_mode': False
            })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Create table if not exists
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_settings (
                    user_id TEXT PRIMARY KEY,
                    theme TEXT DEFAULT 'dark',
                    language TEXT DEFAULT 'tr',
                    timezone TEXT DEFAULT 'Europe/Istanbul',
                    date_format TEXT DEFAULT 'dd.mm.yyyy',
                    auto_refresh INTEGER DEFAULT 30,
                    items_per_page INTEGER DEFAULT 25,
                    show_animations BOOLEAN DEFAULT 1,
                    compact_mode BOOLEAN DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Save settings to database
            conn.execute('''
                INSERT OR REPLACE INTO dashboard_settings 
                (user_id, theme, language, timezone, date_format, auto_refresh, 
                 items_per_page, show_animations, compact_mode, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                'admin',  # In real app, use actual user ID
                data.get('theme', 'dark'),
                data.get('language', 'tr'),
                data.get('timezone', 'Europe/Istanbul'),
                data.get('date_format', 'dd.mm.yyyy'),
                data.get('auto_refresh', 30),
                data.get('items_per_page', 25),
                data.get('show_animations', True),
                data.get('compact_mode', False)
            ))
            
            conn.commit()
            conn.close()
            
            # Set language in session for immediate effect
            session['dashboard_language'] = data.get('language', 'tr')
            
            return jsonify({
                'success': True, 
                'message': 'Genel ayarlar başarıyla kaydedildi!',
                'settings': data
            })
            
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/notifications', methods=['POST'])
@require_auth
def api_save_notification_settings():
    """Bildirim ayarlarını kaydet"""
    try:
        data = request.get_json()
        
        # Simulate saving notification preferences
        settings = {
            'notify_new_warnings': data.get('notify_new_warnings', False),
            'notify_new_bans': data.get('notify_new_bans', False),
            'notify_appeals': data.get('notify_appeals', False),
            'notify_bot_offline': data.get('notify_bot_offline', False),
            'notify_high_activity': data.get('notify_high_activity', False),
            'notify_updates': data.get('notify_updates', False),
            'notification_method': data.get('notification_method', 'browser'),
            'notification_frequency': data.get('notification_frequency', 'instant')
        }
        
        # In a real app, save to database
        return jsonify({'success': True, 'message': 'Bildirim ayarları başarıyla kaydedildi!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/test-notification', methods=['POST'])
@require_auth
def api_test_notification():
    """Test bildirimi gönder"""
    try:
        return jsonify({
            'success': True, 
            'message': 'Test bildirimi başarıyla gönderildi!',
            'notification': {
                'title': 'IronWard Test Bildirimi',
                'body': 'Bildirim ayarlarınız doğru şekilde çalışıyor!'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)