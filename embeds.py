import discord
from datetime import datetime

def create_embed(title=None, description=None, color=None, **kwargs):
    """Create a standardized embed."""
    if color is None:
        color = discord.Color.blue()
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    # Add fields from kwargs
    for key, value in kwargs.items():
        if key.startswith('field_'):
            field_name = key.replace('field_', '').replace('_', ' ').title()
            embed.add_field(name=field_name, value=value, inline=True)
    
    return embed

def create_success_embed(title, description=None):
    """Create a success embed."""
    return create_embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green()
    )

def create_error_embed(title, description=None):
    """Create an error embed."""
    return create_embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red()
    )

def create_warning_embed(title, description=None):
    """Create a warning embed."""
    return create_embed(
        title=f"⚠️ {title}",
        description=description,
        color=discord.Color.orange()
    )

def create_info_embed(title, description=None):
    """Create an info embed."""
    return create_embed(
        title=f"ℹ️ {title}",
        description=description,
        color=discord.Color.blue()
    )

def create_moderation_embed(action, user, moderator, reason=None, duration=None):
    """Create a moderation action embed."""
    colors = {
        'BAN': discord.Color.red(),
        'KICK': discord.Color.orange(),
        'MUTE': discord.Color.dark_orange(),
        'WARN': discord.Color.yellow(),
        'UNBAN': discord.Color.green(),
        'UNMUTE': discord.Color.green()
    }
    
    emojis = {
        'BAN': '🔨',
        'KICK': '👢', 
        'MUTE': '🔇',
        'WARN': '⚠️',
        'UNBAN': '✅',
        'UNMUTE': '🔊'
    }
    
    color = colors.get(action, discord.Color.blue())
    emoji = emojis.get(action, '⚖️')
    
    embed = discord.Embed(
        title=f"{emoji} {action.title()}",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="👤 Kullanıcı", value=str(user), inline=True)
    embed.add_field(name="👮 Moderatör", value=str(moderator), inline=True)
    
    if reason:
        embed.add_field(name="📝 Sebep", value=reason, inline=False)
    
    if duration:
        embed.add_field(name="⏱️ Süre", value=duration, inline=True)
    
    if hasattr(user, 'display_avatar'):
        embed.set_thumbnail(url=user.display_avatar.url)
    
    return embed

def create_user_info_embed(member):
    """Create a user info embed."""
    embed = discord.Embed(
        title=f"👤 {member.display_name}",
        color=member.color or discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Hesap Oluşturma", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    
    if member.joined_at:
        embed.add_field(name="📅 Sunucuya Katılma", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
    
    embed.add_field(name="📊 Durum", value=str(member.status).title(), inline=True)
    
    if member.nick:
        embed.add_field(name="📝 Takma Ad", value=member.nick, inline=True)
    
    # Top role
    if len(member.roles) > 1:
        embed.add_field(name="🏷️ En Yüksek Rol", value=member.top_role.mention, inline=True)
    
    return embed

def create_server_info_embed(guild):
    """Create a server info embed."""
    embed = discord.Embed(
        title=f"🏰 {guild.name}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="👑 Sahip", value=guild.owner.mention if guild.owner else "Bilinmiyor", inline=True)
    embed.add_field(name="📅 Oluşturulma", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    
    # Member count
    online_count = sum(1 for member in guild.members if member.status != discord.Status.offline)
    embed.add_field(name="👥 Üyeler", value=f"Toplam: {guild.member_count}\nÇevrimiçi: {online_count}", inline=True)
    
    # Channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    embed.add_field(name="📺 Kanallar", value=f"Metin: {text_channels}\nSes: {voice_channels}", inline=True)
    
    embed.add_field(name="🏷️ Roller", value=len(guild.roles), inline=True)
    embed.add_field(name="🚀 Boost", value=guild.premium_subscription_count, inline=True)
    embed.add_field(name="📈 Boost Seviyesi", value=guild.premium_tier, inline=True)
    
    return embed
