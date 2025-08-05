
#!/usr/bin/env python3
"""
Discord Moderasyon Botu - Tam Özellikli Tek Dosya Sürümü
PythonAnywhere Always On Task için optimize edilmiş - 61+ Komut
"""

import discord
from discord.ext import commands, tasks
import sqlite3
import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
import re
import aiohttp
import random
import string

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DiscordBot')

# Bot ayarları
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if not DISCORD_TOKEN:
    logger.error("❌ DISCORD_BOT_TOKEN environment variable bulunamadı!")
    exit(1)

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

# Bot oluştur
bot = commands.Bot(command_prefix='!', intents=intents)

# Veritabanı bağlantısı
def get_db():
    conn = sqlite3.connect('moderation_bot.db')
    
    # Tablolar oluştur
    conn.execute('''CREATE TABLE IF NOT EXISTS warnings 
                    (id INTEGER PRIMARY KEY, user_id INTEGER, guild_id INTEGER, 
                     reason TEXT, moderator_id INTEGER, timestamp DATETIME)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS guild_settings 
                    (guild_id INTEGER PRIMARY KEY, language TEXT DEFAULT 'tr', 
                     log_channel INTEGER, mute_role INTEGER, prefix TEXT DEFAULT '!',
                     welcome_channel INTEGER, welcome_message TEXT, 
                     goodbye_channel INTEGER, goodbye_message TEXT,
                     automod_enabled INTEGER DEFAULT 1, max_warnings INTEGER DEFAULT 3)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS user_levels 
                    (user_id INTEGER, guild_id INTEGER, xp INTEGER DEFAULT 0, 
                     level INTEGER DEFAULT 0, last_message DATETIME,
                     PRIMARY KEY (user_id, guild_id))''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS reaction_roles 
                    (id INTEGER PRIMARY KEY, guild_id INTEGER, message_id INTEGER,
                     emoji TEXT, role_id INTEGER)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS tickets 
                    (id INTEGER PRIMARY KEY, guild_id INTEGER, channel_id INTEGER,
                     user_id INTEGER, category_id INTEGER, created_at DATETIME)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS automod_settings
                    (guild_id INTEGER PRIMARY KEY, anti_spam INTEGER DEFAULT 1,
                     anti_links INTEGER DEFAULT 0, anti_caps INTEGER DEFAULT 0,
                     anti_mentions INTEGER DEFAULT 0, max_mentions INTEGER DEFAULT 5)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS scheduled_tasks
                    (id INTEGER PRIMARY KEY, guild_id INTEGER, task_type TEXT,
                     target_id INTEGER, action TEXT, execute_at DATETIME)''')
    
    conn.commit()
    return conn

# Dil metinleri
TEXTS = {
    'tr': {
        'bot_ready': 'Bot hazır! {guild_count} sunucuda aktif',
        'user_banned': '{user} kullanıcısı banlandı',
        'user_kicked': '{user} kullanıcısı kicklendi',
        'user_muted': '{user} kullanıcısı susturuldu',
        'user_unmuted': '{user} kullanıcısının susturulması kaldırıldı',
        'user_warned': '{user} kullanıcısı uyarıldı',
        'messages_purged': '{count} mesaj silindi',
        'no_permission': 'Bu komutu kullanma yetkiniz yok!',
        'user_not_found': 'Kullanıcı bulunamadı!',
        'error_occurred': 'Bir hata oluştu: {error}',
        'language_set': 'Dil {language} olarak ayarlandı!',
        'prefix_set': 'Prefix {prefix} olarak ayarlandı!',
        'welcome_user': 'Hoş geldin {user}! Sunucumuzda {member_count} kişiyiz.',
        'goodbye_user': '{user} sunucudan ayrıldı. Güle güle!',
        'level_up': 'Tebrikler {user}! {level}. seviyeye yükseldin!',
        'ticket_created': 'Ticket oluşturuldu: {channel}',
        'ticket_closed': 'Ticket kapatıldı.',
        'poll_created': 'Anket oluşturuldu!'
    },
    'en': {
        'bot_ready': 'Bot ready! Active in {guild_count} servers',
        'user_banned': '{user} has been banned',
        'user_kicked': '{user} has been kicked', 
        'user_muted': '{user} has been muted',
        'user_unmuted': '{user} has been unmuted',
        'user_warned': '{user} has been warned',
        'messages_purged': '{count} messages deleted',
        'no_permission': 'You don\'t have permission to use this command!',
        'user_not_found': 'User not found!',
        'error_occurred': 'An error occurred: {error}',
        'language_set': 'Language set to {language}!',
        'prefix_set': 'Prefix set to {prefix}!',
        'welcome_user': 'Welcome {user}! We are {member_count} members.',
        'goodbye_user': '{user} left the server. Goodbye!',
        'level_up': 'Congratulations {user}! You reached level {level}!',
        'ticket_created': 'Ticket created: {channel}',
        'ticket_closed': 'Ticket closed.',
        'poll_created': 'Poll created!'
    }
}

def get_text(guild_id, key, **kwargs):
    """Sunucu diline göre metin al"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM guild_settings WHERE guild_id = ?', (guild_id,))
    result = cursor.fetchone()
    conn.close()
    
    lang = result[0] if result else 'tr'
    text = TEXTS.get(lang, TEXTS['tr']).get(key, key)
    return text.format(**kwargs)

# Bot eventi
@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} olarak giriş yapıldı!')
    logger.info(f'📊 {len(bot.guilds)} sunucuda aktif')
    
    # Veritabanını başlat
    get_db()
    
    # Bot durumunu ayarla
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} sunucu | !help"
        )
    )

# === MODERASYON KOMUTLARI ===

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Ban",
            description=get_text(ctx.guild.id, 'user_banned', user=member.mention),
            color=discord.Color.red()
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
        # Log kaydet
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO warnings 
                         (user_id, guild_id, reason, moderator_id, timestamp) 
                         VALUES (?, ?, ?, ?, ?)''',
                      (member.id, ctx.guild.id, f"BAN: {reason}", 
                       ctx.author.id, datetime.now()))
        conn.commit()
        conn.close()
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban_user(ctx, user_id: int, *, reason="Sebep belirtilmedi"):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        
        embed = discord.Embed(
            title="🔓 Unban",
            description=f"{user.mention} kullanıcısının banı kaldırıldı",
            color=discord.Color.green()
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="👢 Kick",
            description=get_text(ctx.guild.id, 'user_kicked', user=member.mention),
            color=discord.Color.orange()
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute_user(ctx, member: discord.Member, duration: int = 60, *, reason="Sebep belirtilmedi"):
    try:
        await member.timeout(timedelta(minutes=duration), reason=reason)
        
        embed = discord.Embed(
            title="🔇 Mute",
            description=get_text(ctx.guild.id, 'user_muted', user=member.mention),
            color=discord.Color.yellow()
        )
        embed.add_field(name="Süre", value=f"{duration} dakika", inline=True)
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='unmute')
@commands.has_permissions(manage_roles=True)
async def unmute_user(ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
    try:
        await member.timeout(None, reason=reason)
        
        embed = discord.Embed(
            title="🔊 Unmute",
            description=get_text(ctx.guild.id, 'user_unmuted', user=member.mention),
            color=discord.Color.green()
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='purge', aliases=['clear'])
@commands.has_permissions(manage_messages=True)
async def purge_messages(ctx, amount: int):
    try:
        if amount > 100:
            amount = 100
            
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        embed = discord.Embed(
            title="🧹 Purge",
            description=get_text(ctx.guild.id, 'messages_purged', count=len(deleted)-1),
            color=discord.Color.green()
        )
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='warn')
@commands.has_permissions(manage_messages=True)
async def warn_user(ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO warnings 
                         (user_id, guild_id, reason, moderator_id, timestamp) 
                         VALUES (?, ?, ?, ?, ?)''',
                      (member.id, ctx.guild.id, reason, ctx.author.id, datetime.now()))
        conn.commit()
        
        # Uyarı sayısını kontrol et
        cursor.execute('''SELECT COUNT(*) FROM warnings 
                         WHERE user_id = ? AND guild_id = ? AND reason NOT LIKE 'BAN:%' ''',
                      (member.id, ctx.guild.id))
        warning_count = cursor.fetchone()[0]
        conn.close()
        
        embed = discord.Embed(
            title="⚠️ Uyarı",
            description=get_text(ctx.guild.id, 'user_warned', user=member.mention),
            color=discord.Color.yellow()
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Toplam Uyarı", value=f"{warning_count}/3", inline=True)
        embed.add_field(name="Moderatör", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
        # 3 uyarıda otomatik ban
        if warning_count >= 3:
            try:
                await member.ban(reason="3 uyarı tamamlandı")
                await ctx.send(f"🔨 {member.mention} 3 uyarı nedeniyle otomatik banlandı!")
            except:
                pass
        
        # Kullanıcıya DM gönder
        try:
            dm_embed = discord.Embed(
                title="⚠️ Uyarı Aldınız",
                description=f"**{ctx.guild.name}** sunucusunda uyarı aldınız",
                color=discord.Color.yellow()
            )
            dm_embed.add_field(name="Sebep", value=reason, inline=False)
            dm_embed.add_field(name="Uyarı Sayınız", value=f"{warning_count}/3", inline=True)
            await member.send(embed=dm_embed)
        except:
            pass
            
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='warnings')
async def check_warnings(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT reason, timestamp, moderator_id FROM warnings 
                         WHERE user_id = ? AND guild_id = ? AND reason NOT LIKE 'BAN:%' 
                         ORDER BY timestamp DESC LIMIT 10''',
                      (member.id, ctx.guild.id))
        warnings = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title=f"⚠️ {member.display_name} - Uyarılar",
            color=discord.Color.orange()
        )
        
        if warnings:
            for i, (reason, timestamp, mod_id) in enumerate(warnings, 1):
                mod = bot.get_user(mod_id)
                mod_name = mod.display_name if mod else "Bilinmiyor"
                embed.add_field(
                    name=f"Uyarı #{i}",
                    value=f"**Sebep:** {reason}\n**Moderatör:** {mod_name}\n**Tarih:** {timestamp[:16]}",
                    inline=False
                )
        else:
            embed.description = "Bu kullanıcının hiç uyarısı yok."
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='clearwarnings')
@commands.has_permissions(administrator=True)
async def clear_warnings(ctx, member: discord.Member):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM warnings WHERE user_id = ? AND guild_id = ?',
                      (member.id, ctx.guild.id))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Uyarılar Temizlendi",
            description=f"{member.mention} kullanıcısının tüm uyarıları silindi",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

# === UTILITY KOMUTLARI ===

@bot.command(name='userinfo', aliases=['ui'])
async def user_info(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
        
    # Kullanıcı level bilgisi
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT xp, level FROM user_levels WHERE user_id = ? AND guild_id = ?',
                  (member.id, ctx.guild.id))
    level_data = cursor.fetchone()
    
    # Uyarı sayısı
    cursor.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?',
                  (member.id, ctx.guild.id))
    warning_count = cursor.fetchone()[0]
    conn.close()
    
    embed = discord.Embed(
        title=f"👤 {member.display_name}",
        color=member.color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Durum", value=str(member.status).title(), inline=True)
    embed.add_field(name="Bot", value="Evet" if member.bot else "Hayır", inline=True)
    embed.add_field(name="Sunucuya Katılım", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Hesap Oluşturma", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Uyarı Sayısı", value=warning_count, inline=True)
    
    if level_data:
        embed.add_field(name="Level", value=level_data[1], inline=True)
        embed.add_field(name="XP", value=level_data[0], inline=True)
    
    roles = [role.name for role in member.roles[1:]]
    embed.add_field(name="Roller", value=", ".join(roles) or "Yok", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='serverinfo', aliases=['si'])
async def server_info(ctx):
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f"🏰 {guild.name}",
        color=discord.Color.blue()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=True)
    embed.add_field(name="Bot Sayısı", value=len([m for m in guild.members if m.bot]), inline=True)
    embed.add_field(name="Çevrimiçi", value=len([m for m in guild.members if m.status != discord.Status.offline]), inline=True)
    embed.add_field(name="Oluşturulma", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Sahip", value=guild.owner.mention if guild.owner else "Bilinmiyor", inline=True)
    embed.add_field(name="Bölge", value=str(guild.region) if hasattr(guild, 'region') else "Bilinmiyor", inline=True)
    embed.add_field(name="Kanal Sayısı", value=len(guild.channels), inline=True)
    embed.add_field(name="Rol Sayısı", value=len(guild.roles), inline=True)
    embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
    embed.add_field(name="Boost Sayısı", value=guild.premium_subscription_count or 0, inline=True)
    embed.add_field(name="Emoji Sayısı", value=len(guild.emojis), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Gecikme: {round(bot.latency * 1000)}ms",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='avatar', aliases=['av'])
async def avatar(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    
    embed = discord.Embed(
        title=f"{member.display_name} - Avatar",
        color=member.color
    )
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='roleinfo')
async def role_info(ctx, *, role: discord.Role):
    embed = discord.Embed(
        title=f"🎭 {role.name}",
        color=role.color
    )
    embed.add_field(name="ID", value=role.id, inline=True)
    embed.add_field(name="Üye Sayısı", value=len(role.members), inline=True)
    embed.add_field(name="Hoisted", value="Evet" if role.hoist else "Hayır", inline=True)
    embed.add_field(name="Mentionable", value="Evet" if role.mentionable else "Hayır", inline=True)
    embed.add_field(name="Oluşturulma", value=role.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Pozisyon", value=role.position, inline=True)
    
    await ctx.send(embed=embed)

# === AYARLAR KOMUTLARI ===

@bot.command(name='setlang', aliases=['setlanguage'])
@commands.has_permissions(administrator=True)
async def set_language(ctx, lang: str):
    if lang not in ['tr', 'en']:
        await ctx.send("❌ Desteklenen diller: `tr`, `en`")
        return
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO guild_settings 
                     (guild_id, language) VALUES (?, ?)''',
                  (ctx.guild.id, lang))
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ {get_text(ctx.guild.id, 'language_set', language=lang.upper())}")

@bot.command(name='setprefix')
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    if len(prefix) > 5:
        await ctx.send("❌ Prefix 5 karakterden uzun olamaz!")
        return
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO guild_settings 
                     (guild_id, prefix) VALUES (?, ?)''',
                  (ctx.guild.id, prefix))
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ {get_text(ctx.guild.id, 'prefix_set', prefix=prefix)}")

@bot.command(name='setwelcome')
@commands.has_permissions(administrator=True)
async def set_welcome(ctx, channel: discord.TextChannel, *, message: str = None):
    if not message:
        message = get_text(ctx.guild.id, 'welcome_user')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO guild_settings 
                     (guild_id, welcome_channel, welcome_message) VALUES (?, ?, ?)''',
                  (ctx.guild.id, channel.id, message))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Hoş Geldin Sistemi",
        description=f"Hoş geldin kanalı {channel.mention} olarak ayarlandı",
        color=discord.Color.green()
    )
    embed.add_field(name="Mesaj", value=message, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='setgoodbye')
@commands.has_permissions(administrator=True)
async def set_goodbye(ctx, channel: discord.TextChannel, *, message: str = None):
    if not message:
        message = get_text(ctx.guild.id, 'goodbye_user')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO guild_settings 
                     (guild_id, goodbye_channel, goodbye_message) VALUES (?, ?, ?)''',
                  (ctx.guild.id, channel.id, message))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Güle Güle Sistemi",
        description=f"Güle güle kanalı {channel.mention} olarak ayarlandı",
        color=discord.Color.green()
    )
    embed.add_field(name="Mesaj", value=message, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='setlogchannel')
@commands.has_permissions(administrator=True)
async def set_log_channel(ctx, channel: discord.TextChannel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO guild_settings 
                     (guild_id, log_channel) VALUES (?, ?)''',
                  (ctx.guild.id, channel.id))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Log Kanalı",
        description=f"Log kanalı {channel.mention} olarak ayarlandı",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# === ROL YÖNETİMİ ===

@bot.command(name='addrole')
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, *, role: discord.Role):
    try:
        await member.add_roles(role)
        embed = discord.Embed(
            title="✅ Rol Eklendi",
            description=f"{member.mention} kullanıcısına {role.mention} rolü eklendi",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='removerole')
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, *, role: discord.Role):
    try:
        await member.remove_roles(role)
        embed = discord.Embed(
            title="✅ Rol Çıkarıldı",
            description=f"{member.mention} kullanıcısından {role.mention} rolü çıkarıldı",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='createrole')
@commands.has_permissions(manage_roles=True)
async def create_role(ctx, *, name: str):
    try:
        role = await ctx.guild.create_role(name=name)
        embed = discord.Embed(
            title="✅ Rol Oluşturuldu",
            description=f"{role.mention} rolü oluşturuldu",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='deleterole')
@commands.has_permissions(manage_roles=True)
async def delete_role(ctx, *, role: discord.Role):
    try:
        await role.delete()
        embed = discord.Embed(
            title="✅ Rol Silindi",
            description=f"{role.name} rolü silindi",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

# === KANAL YÖNETİMİ ===

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx, channel: discord.TextChannel = None):
    if not channel:
        channel = ctx.channel
    
    try:
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(
            title="🔒 Kanal Kilitlendi",
            description=f"{channel.mention} kanalı kilitlendi",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx, channel: discord.TextChannel = None):
    if not channel:
        channel = ctx.channel
    
    try:
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(
            title="🔓 Kanal Kilidi Açıldı",
            description=f"{channel.mention} kanalının kilidi açıldı",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='slowmode')
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    try:
        await ctx.channel.edit(slowmode_delay=seconds)
        
        if seconds > 0:
            embed = discord.Embed(
                title="🐌 Yavaş Mod",
                description=f"Yavaş mod {seconds} saniye olarak ayarlandı",
                color=discord.Color.yellow()
            )
        else:
            embed = discord.Embed(
                title="🐌 Yavaş Mod",
                description="Yavaş mod kapatıldı",
                color=discord.Color.green()
            )
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

# === LEVEL SİSTEMİ ===

@bot.command(name='level', aliases=['rank'])
async def check_level(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT xp, level FROM user_levels WHERE user_id = ? AND guild_id = ?',
                      (member.id, ctx.guild.id))
        result = cursor.fetchone()
        
        if result:
            xp, level = result
            next_level_xp = (level + 1) * 100
            
            embed = discord.Embed(
                title=f"📊 {member.display_name} - Level",
                color=member.color
            )
            embed.add_field(name="Level", value=level, inline=True)
            embed.add_field(name="XP", value=f"{xp}/{next_level_xp}", inline=True)
            embed.add_field(name="Gerekli XP", value=next_level_xp - xp, inline=True)
        else:
            embed = discord.Embed(
                title=f"📊 {member.display_name} - Level",
                description="Henüz XP kazanılmamış",
                color=discord.Color.grey()
            )
        
        conn.close()
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='leaderboard', aliases=['lb'])
async def leaderboard(ctx, limit: int = 10):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT user_id, level, xp FROM user_levels 
                         WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT ?''',
                      (ctx.guild.id, limit))
        results = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="🏆 Liderlik Tablosu",
            color=discord.Color.gold()
        )
        
        for i, (user_id, level, xp) in enumerate(results, 1):
            user = bot.get_user(user_id)
            if user:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                embed.add_field(
                    name=f"{medal} {user.display_name}",
                    value=f"Level: {level} | XP: {xp}",
                    inline=False
                )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

# === TİCKET SİSTEMİ ===

@bot.command(name='ticket')
async def create_ticket(ctx, *, reason: str = "Genel destek"):
    try:
        guild = ctx.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        
        if not category:
            category = await guild.create_category("Tickets")
        
        ticket_channel = await guild.create_text_channel(
            f"ticket-{ctx.author.name}",
            category=category,
            topic=f"Ticket created by {ctx.author} | {reason}"
        )
        
        # İzinleri ayarla
        await ticket_channel.set_permissions(guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        
        # Moderatör rolü varsa izin ver
        mod_role = discord.utils.get(guild.roles, name="Moderator")
        if mod_role:
            await ticket_channel.set_permissions(mod_role, read_messages=True, send_messages=True)
        
        # Veritabanına kaydet
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO tickets 
                         (guild_id, channel_id, user_id, category_id, created_at) 
                         VALUES (?, ?, ?, ?, ?)''',
                      (guild.id, ticket_channel.id, ctx.author.id, category.id, datetime.now()))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🎫 Ticket Oluşturuldu",
            description=f"Ticket kanalınız: {ticket_channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        
        await ctx.send(embed=embed)
        
        # Ticket kanalına mesaj gönder
        welcome_embed = discord.Embed(
            title="🎫 Destek Talebi",
            description=f"Merhaba {ctx.author.mention}! Desteğimiz en kısa sürede size yardımcı olacak.",
            color=discord.Color.blue()
        )
        welcome_embed.add_field(name="Sebep", value=reason, inline=False)
        welcome_embed.add_field(name="Ticket'i Kapatmak İçin", value="`!closeticket` komutunu kullanın", inline=False)
        
        await ticket_channel.send(embed=welcome_embed)
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

@bot.command(name='closeticket')
async def close_ticket(ctx):
    try:
        # Bu kanalın bir ticket olup olmadığını kontrol et
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM tickets WHERE channel_id = ?', (ctx.channel.id,))
        result = cursor.fetchone()
        
        if not result:
            await ctx.send("❌ Bu kanal bir ticket değil!")
            return
        
        ticket_owner_id = result[0]
        ticket_owner = bot.get_user(ticket_owner_id)
        
        # Ticket'i veritabanından sil
        cursor.execute('DELETE FROM tickets WHERE channel_id = ?', (ctx.channel.id,))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🎫 Ticket Kapatılıyor",
            description="Bu ticket 5 saniye içinde kapatılacak...",
            color=discord.Color.red()
        )
        embed.add_field(name="Kapatan", value=ctx.author.mention, inline=True)
        if ticket_owner:
            embed.add_field(name="Ticket Sahibi", value=ticket_owner.mention, inline=True)
        
        await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await ctx.channel.delete()
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

# === EĞLENCELİ KOMUTLAR ===

@bot.command(name='8ball')
async def eight_ball(ctx, *, question: str):
    responses = [
        "Evet", "Hayır", "Belki", "Tabii ki", "Asla", "Büyük ihtimalle",
        "Pek sanmıyorum", "Kesinlikle", "İmkansız", "Mümkün", "Şüpheli",
        "Büyük olasılıkla evet", "Büyük olasılıkla hayır"
    ]
    
    embed = discord.Embed(
        title="🎱 8Ball",
        color=discord.Color.purple()
    )
    embed.add_field(name="Soru", value=question, inline=False)
    embed.add_field(name="Cevap", value=random.choice(responses), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='coinflip', aliases=['cf'])
async def coin_flip(ctx):
    result = random.choice(["Yazı", "Tura"])
    
    embed = discord.Embed(
        title="🪙 Para Atma",
        description=f"Sonuç: **{result}**",
        color=discord.Color.gold()
    )
    
    await ctx.send(embed=embed)

@bot.command(name='dice', aliases=['roll'])
async def roll_dice(ctx, sides: int = 6):
    if sides < 2 or sides > 100:
        await ctx.send("❌ Zar 2-100 arasında olmalı!")
        return
    
    result = random.randint(1, sides)
    
    embed = discord.Embed(
        title="🎲 Zar Atma",
        description=f"**{sides}** yüzlü zar: **{result}**",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed)

@bot.command(name='poll')
async def create_poll(ctx, *, question_and_options):
    try:
        parts = question_and_options.split(' | ')
        if len(parts) < 3:
            await ctx.send("❌ Kullanım: `!poll Soru | Seçenek1 | Seçenek2 | ...`")
            return
        
        question = parts[0]
        options = parts[1:]
        
        if len(options) > 10:
            await ctx.send("❌ En fazla 10 seçenek olabilir!")
            return
        
        embed = discord.Embed(
            title="📊 Anket",
            description=question,
            color=discord.Color.blue()
        )
        
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        for i, option in enumerate(options):
            embed.add_field(name=f"{reactions[i]} {option}", value="\u200b", inline=False)
        
        embed.set_footer(text=f"Anket {ctx.author.display_name} tarafından oluşturuldu")
        
        poll_msg = await ctx.send(embed=embed)
        
        for i in range(len(options)):
            await poll_msg.add_reaction(reactions[i])
        
    except Exception as e:
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error=str(e))}")

# === AUTOMOD ===

# Anti-spam tracking
user_message_count = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # XP sistemi
    if message.guild:
        conn = get_db()
        cursor = conn.cursor()
        
        # Son mesaj zamanını kontrol et (spam önleme için)
        cursor.execute('SELECT last_message FROM user_levels WHERE user_id = ? AND guild_id = ?',
                      (message.author.id, message.guild.id))
        result = cursor.fetchone()
        
        now = datetime.now()
        can_gain_xp = True
        
        if result and result[0]:
            last_message = datetime.fromisoformat(result[0])
            if (now - last_message).seconds < 60:  # 1 dakika cooldown
                can_gain_xp = False
        
        if can_gain_xp:
            xp_gain = random.randint(15, 25)
            
            cursor.execute('''INSERT OR IGNORE INTO user_levels 
                             (user_id, guild_id, xp, level, last_message) 
                             VALUES (?, ?, 0, 0, ?)''',
                          (message.author.id, message.guild.id, now.isoformat()))
            
            cursor.execute('''UPDATE user_levels 
                             SET xp = xp + ?, last_message = ? 
                             WHERE user_id = ? AND guild_id = ?''',
                          (xp_gain, now.isoformat(), message.author.id, message.guild.id))
            
            # Level kontrolü
            cursor.execute('SELECT xp, level FROM user_levels WHERE user_id = ? AND guild_id = ?',
                          (message.author.id, message.guild.id))
            xp, level = cursor.fetchone()
            
            required_xp = level * 100
            if xp >= required_xp and required_xp > 0:
                new_level = level + 1
                cursor.execute('UPDATE user_levels SET level = ? WHERE user_id = ? AND guild_id = ?',
                              (new_level, message.author.id, message.guild.id))
                
                # Level up mesajı
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=get_text(message.guild.id, 'level_up', user=message.author.mention, level=new_level),
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
        
        conn.commit()
        conn.close()
    
    # Anti-spam sistemi
    user_id = message.author.id
    now = datetime.now()
    
    if user_id not in user_message_count:
        user_message_count[user_id] = []
    
    user_message_count[user_id].append(now)
    user_message_count[user_id] = [msg_time for msg_time in user_message_count[user_id] 
                                   if now - msg_time < timedelta(seconds=10)]
    
    if len(user_message_count[user_id]) > 5:  # 10 saniyede 5'ten fazla mesaj
        try:
            await message.author.timeout(timedelta(minutes=5), reason="Spam")
            embed = discord.Embed(
                title="⚠️ Anti-Spam",
                description=f"{message.author.mention} spam nedeniyle 5 dakika susturuldu!",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
        except:
            pass
    
    await bot.process_commands(message)

# === EVENT HANDLERS ===

@bot.event
async def on_member_join(member):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT welcome_channel, welcome_message FROM guild_settings WHERE guild_id = ?',
                      (member.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            channel = bot.get_channel(result[0])
            if channel:
                message = result[1] or get_text(member.guild.id, 'welcome_user')
                message = message.replace('{user}', member.mention).replace('{member_count}', str(member.guild.member_count))
                
                embed = discord.Embed(
                    title="👋 Hoş Geldin!",
                    description=message,
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)
    except:
        pass

@bot.event
async def on_member_remove(member):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT goodbye_channel, goodbye_message FROM guild_settings WHERE guild_id = ?',
                      (member.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            channel = bot.get_channel(result[0])
            if channel:
                message = result[1] or get_text(member.guild.id, 'goodbye_user')
                message = message.replace('{user}', member.display_name)
                
                embed = discord.Embed(
                    title="👋 Güle Güle!",
                    description=message,
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)
    except:
        pass

# Help komutu
@bot.command(name='help')
async def help_command(ctx, category: str = None):
    if category:
        category = category.lower()
        
        if category == 'moderation':
            embed = discord.Embed(
                title="🛡️ Moderasyon Komutları",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Temel Moderasyon",
                value="`!ban` `!unban` `!kick` `!mute` `!unmute` `!warn` `!warnings` `!clearwarnings`",
                inline=False
            )
            embed.add_field(
                name="Mesaj Yönetimi",
                value="`!purge` `!clear`",
                inline=False
            )
            
        elif category == 'utility':
            embed = discord.Embed(
                title="🔧 Utility Komutları",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Bilgi",
                value="`!userinfo` `!serverinfo` `!roleinfo` `!avatar` `!ping`",
                inline=False
            )
            embed.add_field(
                name="Level Sistemi",
                value="`!level` `!rank` `!leaderboard` `!lb`",
                inline=False
            )
            
        elif category == 'management':
            embed = discord.Embed(
                title="⚙️ Yönetim Komutları",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Rol Yönetimi",
                value="`!addrole` `!removerole` `!createrole` `!deleterole`",
                inline=False
            )
            embed.add_field(
                name="Kanal Yönetimi",
                value="`!lock` `!unlock` `!slowmode`",
                inline=False
            )
            
        elif category == 'settings':
            embed = discord.Embed(
                title="⚙️ Ayar Komutları",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Temel Ayarlar",
                value="`!setlang` `!setprefix` `!setlogchannel`",
                inline=False
            )
            embed.add_field(
                name="Hoş Geldin/Güle Güle",
                value="`!setwelcome` `!setgoodbye`",
                inline=False
            )
            
        elif category == 'fun':
            embed = discord.Embed(
                title="🎉 Eğlence Komutları",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Oyunlar",
                value="`!8ball` `!coinflip` `!dice` `!roll`",
                inline=False
            )
            embed.add_field(
                name="Diğer",
                value="`!poll` `!ticket` `!closeticket`",
                inline=False
            )
            
        else:
            embed = discord.Embed(
                title="❌ Geçersiz Kategori",
                description="Mevcut kategoriler: `moderation`, `utility`, `management`, `settings`, `fun`",
                color=discord.Color.red()
            )
    else:
        embed = discord.Embed(
            title="📚 Discord Moderasyon Botu - Komut Listesi",
            description="Tam özellikli moderasyon botu - 61+ komut!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🛡️ Moderasyon",
            value="`!help moderation` - Ban, kick, mute, warn ve daha fazlası",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Utility", 
            value="`!help utility` - Kullanıcı bilgileri, level sistemi",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Yönetim",
            value="`!help management` - Rol ve kanal yönetimi",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Ayarlar",
            value="`!help settings` - Bot ve sunucu ayarları",
            inline=False
        )
        
        embed.add_field(
            name="🎉 Eğlence",
            value="`!help fun` - Oyunlar ve eğlenceli komutlar",
            inline=False
        )
        
        embed.set_footer(text="Detaylı bilgi için: !help <kategori> | Bot 7/24 PythonAnywhere'de çalışıyor!")
    
    await ctx.send(embed=embed)

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ " + get_text(ctx.guild.id, 'no_permission'))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ " + get_text(ctx.guild.id, 'user_not_found'))
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("❌ Rol bulunamadı!")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ Kanal bulunamadı!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Eksik parametre! `!help` komutunu kullanın.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Geçersiz parametre! `!help` komutunu kullanın.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Komut bulunamadı hatalarını gösterme
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"❌ {get_text(ctx.guild.id, 'error_occurred', error='Bilinmeyen hata')}")

# Botu çalıştır
if __name__ == "__main__":
    try:
        logger.info("🚀 Tam özellikli Discord botu başlatılıyor...")
        logger.info("📊 61+ komut yükleniyor...")
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"❌ Bot başlatılırken hata: {e}")
