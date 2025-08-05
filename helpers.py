import re
from datetime import timedelta

def get_text(languages, lang, key):
    """Get text from language files."""
    try:
        keys = key.split('.')
        text = languages[lang]

        for k in keys:
            text = text[k]

        return text
    except (KeyError, TypeError):
        # Fallback to Turkish if key not found
        try:
            keys = key.split('.')
            text = languages['tr']
            for k in keys:
                text = text[k]
            return text
        except:
            return key

def parse_time(time_str):
    """Parse time string like '1h', '30m', '2d' into seconds."""
    if not time_str:
        return None

    time_str = time_str.lower().strip()

    # Time multipliers
    multipliers = {
        's': 1,         # seconds
        'm': 60,        # minutes  
        'h': 3600,      # hours
        'd': 86400,     # days
        'w': 604800,    # weeks
        'mo': 2592000,  # months (30 days)
        'y': 31536000   # years (365 days)
    }

    total_seconds = 0
    current_number = ""

    for char in time_str:
        if char.isdigit():
            current_number += char
        elif char in multipliers:
            if current_number:
                total_seconds += int(current_number) * multipliers[char]
                current_number = ""

    # Handle 'mo' (months) separately
    if 'mo' in time_str:
        parts = time_str.split('mo')
        if len(parts) >= 2 and parts[0].isdigit():
            total_seconds += int(parts[0]) * multipliers['mo']

    return total_seconds if total_seconds > 0 else None

def format_time(seconds):
    """Format seconds into readable time string."""
    if seconds < 60:
        return f"{seconds} saniye"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} dakika"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} saat"
    else:
        days = seconds // 86400
        return f"{days} gün"

def truncate_text(text, max_length=100):
    """Truncate text if it's too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def clean_content(content):
    """Clean message content for logging."""
    # Remove mentions, emojis, etc.
    content = re.sub(r'<@[!&]?\d+>', '[mention]', content)
    content = re.sub(r'<#\d+>', '[channel]', content)
    content = re.sub(r'<:\w+:\d+>', '[emoji]', content)
    return content[:500]  # Limit length

def get_user_permissions(member):
    """Get user permissions as a list."""
    perms = []
    if member.guild_permissions.administrator:
        perms.append("Administrator")
    if member.guild_permissions.manage_guild:
        perms.append("Manage Server")
    if member.guild_permissions.manage_channels:
        perms.append("Manage Channels")
    if member.guild_permissions.manage_roles:
        perms.append("Manage Roles")
    if member.guild_permissions.ban_members:
        perms.append("Ban Members")
    if member.guild_permissions.kick_members:
        perms.append("Kick Members")
    if member.guild_permissions.manage_messages:
        perms.append("Manage Messages")

    return perms or ["None"]