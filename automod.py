import discord
from discord.ext import commands, tasks
import re
from utils.helpers import get_text
from utils.embeds import create_embed
from datetime import datetime

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}
        self.check_expired_punishments.start()
    
    async def cog_unload(self):
        self.check_expired_punishments.cancel()
    
    @tasks.loop(minutes=1)
    async def check_expired_punishments(self):
        """Check for expired mutes and bans."""
        # Check expired mutes
        expired_mutes = await self.bot.db.get_expired_mutes()
        for guild_id, user_id in expired_mutes:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            
            member = guild.get_member(user_id)
            if not member:
                await self.bot.db.remove_mute(guild_id, user_id)
                continue
            
            settings = await self.bot.db.get_guild_settings(guild_id)
            if settings and settings['mute_role']:
                mute_role = guild.get_role(settings['mute_role'])
                if mute_role and mute_role in member.roles:
                    try:
                        await member.remove_roles(mute_role, reason="Mute expired")
                        await self.bot.db.remove_mute(guild_id, user_id)
                        await self.bot.db.add_mod_log(
                            guild_id, self.bot.user.id, user_id, "AUTO_UNMUTE", "Mute expired"
                        )
                    except discord.Forbidden:
                        pass
        
        # Check expired bans
        expired_bans = await self.bot.db.get_expired_bans()
        for guild_id, user_id in expired_bans:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            
            try:
                user = await self.bot.fetch_user(user_id)
                await guild.unban(user, reason="Temporary ban expired")
                await self.bot.db.remove_temp_ban(guild_id, user_id)
                await self.bot.db.add_mod_log(
                    guild_id, self.bot.user.id, user_id, "AUTO_UNBAN", "Temporary ban expired"
                )
            except (discord.NotFound, discord.Forbidden):
                await self.bot.db.remove_temp_ban(guild_id, user_id)
    
    @check_expired_punishments.before_loop
    async def before_check_expired_punishments(self):
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation message handler."""
        if not message.guild or message.author.bot:
            return
        
        # Skip if user has manage messages permission
        if message.author.guild_permissions.manage_messages:
            return
        
        settings = await self.bot.db.get_automod_settings(message.guild.id)
        if not settings:
            return
        
        lang = await self.bot.db.get_language(message.guild.id)
        violations = []
        
        # Anti-spam check
        if settings['anti_spam']:
            if await self.check_spam(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.spam_detected'))
        
        # Anti-flood check  
        if settings['anti_flood']:
            if await self.check_flood(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.flood_detected'))
        
        # Anti-link check
        if settings['anti_link']:
            if await self.check_links(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.link_detected'))
        
        # Anti-invite check
        if settings['anti_invite']:
            if await self.check_invites(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.invite_detected'))
        
        # Caps filter
        if settings['caps_filter']:
            if await self.check_caps(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.caps_detected'))
        
        # Emoji filter
        if settings['emoji_filter']:
            if await self.check_emoji_spam(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.emoji_spam_detected'))
        
        # Mention filter
        if settings['mention_filter']:
            if await self.check_mention_spam(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.mention_spam_detected'))
        
        # Word filter
        if settings['word_filter']:
            if await self.check_blacklisted_words(message):
                violations.append(get_text(self.bot.languages, lang, 'automod.blacklisted_word_detected'))
        
        # Take action if violations found
        if violations:
            await self.handle_violations(message, violations)
    
    async def check_spam(self, message):
        """Check for spam (repeated messages)."""
        user_id = message.author.id
        content = message.content.lower()
        
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []
        
        self.spam_tracker[user_id].append((content, datetime.now()))
        
        # Keep only last 10 messages from last 30 seconds
        cutoff = datetime.now().timestamp() - 30
        self.spam_tracker[user_id] = [
            (msg, time) for msg, time in self.spam_tracker[user_id][-10:]
            if time.timestamp() > cutoff
        ]
        
        # Check for repeated messages
        if len(self.spam_tracker[user_id]) >= 5:
            recent_messages = [msg for msg, time in self.spam_tracker[user_id][-5:]]
            if len(set(recent_messages)) <= 2:  # Same or very similar messages
                return True
        
        return False
    
    async def check_flood(self, message):
        """Check for message flooding."""
        user_id = message.author.id
        
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []
        
        now = datetime.now()
        self.spam_tracker[user_id].append((message.content, now))
        
        # Check if user sent more than 10 messages in last 10 seconds
        cutoff = now.timestamp() - 10
        recent_count = sum(1 for msg, time in self.spam_tracker[user_id] if time.timestamp() > cutoff)
        
        return recent_count > 10
    
    async def check_links(self, message):
        """Check for links."""
        link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return bool(re.search(link_pattern, message.content))
    
    async def check_invites(self, message):
        """Check for Discord invite links."""
        invite_pattern = r'discord(?:\.gg|app\.com\/invite)\/[a-zA-Z0-9]+'
        return bool(re.search(invite_pattern, message.content))
    
    async def check_caps(self, message):
        """Check for excessive caps."""
        if len(message.content) < 10:
            return False
        
        caps_count = sum(1 for char in message.content if char.isupper())
        caps_ratio = caps_count / len(message.content)
        
        return caps_ratio > 0.7
    
    async def check_emoji_spam(self, message):
        """Check for emoji spam."""
        emoji_pattern = r'<:[^:]+:[0-9]+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
        emojis = re.findall(emoji_pattern, message.content)
        
        return len(emojis) > 10
    
    async def check_mention_spam(self, message):
        """Check for mention spam."""
        return len(message.mentions) > 5
    
    async def check_blacklisted_words(self, message):
        """Check for blacklisted words."""
        blacklisted = await self.bot.db.get_blacklisted_words(message.guild.id)
        content_lower = message.content.lower()
        
        for word in blacklisted:
            if word in content_lower:
                return True
        
        return False
    
    async def handle_violations(self, message, violations):
        """Handle auto-moderation violations."""
        try:
            # Delete the message
            await message.delete()
            
            # Send warning to user
            warning_text = "\n".join(violations)
            embed = create_embed(
                title=f"⚠️ {message.author.mention}",
                description=warning_text,
                color=discord.Color.red()
            )
            
            warning_msg = await message.channel.send(embed=embed)
            
            # Delete warning after 10 seconds
            await warning_msg.delete(delay=10)
            
            # Log the action
            await self.bot.db.add_mod_log(
                message.guild.id, self.bot.user.id, message.author.id, 
                "AUTOMOD", f"Message deleted: {', '.join(violations)}"
            )
            
        except discord.Forbidden:
            pass
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx, toggle: str):
        """Toggle anti-spam."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if toggle.lower() in ['aç', 'on', 'enable', 'açık']:
            await self.bot.db.update_automod_setting(ctx.guild.id, 'anti_spam', True)
            status = "açık"
            color = discord.Color.green()
        elif toggle.lower() in ['kapat', 'off', 'disable', 'kapalı']:
            await self.bot.db.update_automod_setting(ctx.guild.id, 'anti_spam', False)
            status = "kapalı"
            color = discord.Color.red()
        else:
            embed = create_embed(
                title="❌ Geçersiz seçenek!",
                description="Kullanım: `antispam [aç/kapat]`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        embed = create_embed(
            title=f"✅ Anti-spam {status}!",
            color=color
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antilink(self, ctx, toggle: str):
        """Toggle anti-link."""
        if toggle.lower() in ['aç', 'on', 'enable', 'açık']:
            await self.bot.db.update_automod_setting(ctx.guild.id, 'anti_link', True)
            status = "açık"
            color = discord.Color.green()
        elif toggle.lower() in ['kapat', 'off', 'disable', 'kapalı']:
            await self.bot.db.update_automod_setting(ctx.guild.id, 'anti_link', False)
            status = "kapalı"
            color = discord.Color.red()
        else:
            embed = create_embed(
                title="❌ Geçersiz seçenek!",
                description="Kullanım: `antilink [aç/kapat]`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        embed = create_embed(
            title=f"✅ Anti-link {status}!",
            color=color
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antiinvite(self, ctx, toggle: str):
        """Toggle anti-invite."""
        if toggle.lower() in ['aç', 'on', 'enable', 'açık']:
            await self.bot.db.update_automod_setting(ctx.guild.id, 'anti_invite', True)
            status = "açık"
            color = discord.Color.green()
        elif toggle.lower() in ['kapat', 'off', 'disable', 'kapalı']:
            await self.bot.db.update_automod_setting(ctx.guild.id, 'anti_invite', False)
            status = "kapalı"
            color = discord.Color.red()
        else:
            embed = create_embed(
                title="❌ Geçersiz seçenek!",
                description="Kullanım: `antiinvite [aç/kapat]`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        embed = create_embed(
            title=f"✅ Anti-invite {status}!",
            color=color
        )
        await ctx.send(embed=embed)
    
    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx):
        """Show blacklisted words."""
        words = await self.bot.db.get_blacklisted_words(ctx.guild.id)
        
        if not words:
            embed = create_embed(
                title="📝 Kara Liste",
                description="Hiç yasaklı kelime eklenmemiş.",
                color=discord.Color.blue()
            )
        else:
            words_list = ", ".join(f"`{word}`" for word in words)
            embed = create_embed(
                title="📝 Kara Liste",
                description=words_list,
                color=discord.Color.blue()
            )
        
        await ctx.send(embed=embed)
    
    @blacklist.command(name='add')
    @commands.has_permissions(administrator=True)
    async def blacklist_add(self, ctx, *, word):
        """Add word to blacklist."""
        await self.bot.db.add_blacklisted_word(ctx.guild.id, word)
        
        embed = create_embed(
            title=f"✅ `{word}` kara listeye eklendi!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @blacklist.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def blacklist_remove(self, ctx, *, word):
        """Remove word from blacklist."""
        await self.bot.db.remove_blacklisted_word(ctx.guild.id, word)
        
        embed = create_embed(
            title=f"✅ `{word}` kara listeden çıkarıldı!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx):
        """Show auto-moderation settings."""
        settings = await self.bot.db.get_automod_settings(ctx.guild.id)
        
        embed = create_embed(
            title="🤖 Otomatik Moderasyon Ayarları",
            color=discord.Color.purple()
        )
        
        if settings:
            embed.add_field(name="🚫 Anti-Spam", value="✅ Açık" if settings['anti_spam'] else "❌ Kapalı", inline=True)
            embed.add_field(name="🌊 Anti-Flood", value="✅ Açık" if settings['anti_flood'] else "❌ Kapalı", inline=True)
            embed.add_field(name="🔗 Anti-Link", value="✅ Açık" if settings['anti_link'] else "❌ Kapalı", inline=True)
            embed.add_field(name="📨 Anti-Invite", value="✅ Açık" if settings['anti_invite'] else "❌ Kapalı", inline=True)
            embed.add_field(name="🔠 Caps Filter", value="✅ Açık" if settings['caps_filter'] else "❌ Kapalı", inline=True)
            embed.add_field(name="😀 Emoji Filter", value="✅ Açık" if settings['emoji_filter'] else "❌ Kapalı", inline=True)
            embed.add_field(name="👤 Mention Filter", value="✅ Açık" if settings['mention_filter'] else "❌ Kapalı", inline=True)
            embed.add_field(name="📝 Word Filter", value="✅ Açık" if settings['word_filter'] else "❌ Kapalı", inline=True)
        else:
            embed.description = "Otomatik moderasyon ayarları yapılmamış."
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
