import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from utils.helpers import get_text, parse_time
from utils.permissions import hierarchy_check
from utils.embeds import create_embed

class AdvancedModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=['tban'])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tempban(self, ctx, member: discord.Member, duration: str, *, reason="Sebep belirtilmedi"):
        """Temporarily ban a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Hierarchy check
        if not hierarchy_check(ctx.author, member, ctx.guild.owner):
            embed = create_embed(
                title="❌ " + get_text(self.bot.languages, lang, 'errors.hierarchy_error'),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Parse duration
        duration_seconds = parse_time(duration)
        if not duration_seconds:
            embed = create_embed(
                title="❌ Geçersiz süre formatı!",
                description="Örnek: 1h, 30m, 2d, 1w",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Calculate expiry time
        expires_at = datetime.now() + timedelta(seconds=duration_seconds)
        
        # Send DM before ban
        try:
            await member.send(f"🚫 {ctx.guild.name} sunucusundan {duration} süreliğine yasaklandınız!\nSebep: {reason}")
        except:
            pass
        
        # Ban the member
        await member.ban(reason=f"{ctx.author}: {reason} (Temporary: {duration})")
        
        # Add to database
        await self.bot.db.add_temp_ban(ctx.guild.id, member.id, expires_at, reason)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "TEMPBAN", f"{reason} (Duration: {duration})"
        )
        
        # Send success message
        embed = create_embed(
            title=f"✅ {member} {duration} süreliğine yasaklandı!",
            description=f"Sebep: {reason}\nSüre: {expires_at.strftime('%d/%m/%Y %H:%M')} tarihinde kalkacak",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['sban'])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def softban(self, ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
        """Softban a user (ban then immediately unban to delete messages)."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Hierarchy check
        if not hierarchy_check(ctx.author, member, ctx.guild.owner):
            embed = create_embed(
                title="❌ " + get_text(self.bot.languages, lang, 'errors.hierarchy_error'),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Send DM before softban
        try:
            await member.send(f"🚪 {ctx.guild.name} sunucusundan softban edildiniz (mesajlarınız silindi)!\nSebep: {reason}")
        except:
            pass
        
        # Softban (ban then unban)
        await member.ban(reason=f"{ctx.author}: {reason} (Softban)", delete_message_days=7)
        await ctx.guild.unban(member, reason="Softban - Auto unban")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "SOFTBAN", reason
        )
        
        # Send success message
        embed = create_embed(
            title=f"✅ {member} softban edildi!",
            description=f"Sebep: {reason}\nSon 7 günün mesajları silindi",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason="Sebep belirtilmedi"):
        """Timeout a user using Discord's built-in timeout feature."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Hierarchy check
        if not hierarchy_check(ctx.author, member, ctx.guild.owner):
            embed = create_embed(
                title="❌ " + get_text(self.bot.languages, lang, 'errors.hierarchy_error'),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Parse duration
        duration_seconds = parse_time(duration)
        if not duration_seconds or duration_seconds > 2419200:  # Max 28 days
            embed = create_embed(
                title="❌ Geçersiz süre!",
                description="Timeout süresi 1 dakika ile 28 gün arasında olmalı\nÖrnek: 10m, 2h, 1d",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Calculate timeout until
        timeout_until = datetime.now() + timedelta(seconds=duration_seconds)
        
        # Apply timeout
        await member.timeout(timeout_until, reason=f"{ctx.author}: {reason}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "TIMEOUT", f"{reason} (Duration: {duration})"
        )
        
        # Send success message
        embed = create_embed(
            title=f"⏰ {member} {duration} süreliğine timeout edildi!",
            description=f"Sebep: {reason}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Remove timeout from a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if not member.is_timed_out():
            embed = create_embed(
                title="❌ Bu kullanıcı timeout edilmemiş!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Remove timeout
        await member.timeout(None, reason=f"Timeout removed by {ctx.author}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "UNTIMEOUT", "Manual timeout removal"
        )
        
        # Send success message
        embed = create_embed(
            title=f"✅ {member} timeout'u kaldırıldı!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nickname=None):
        """Change user's nickname."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Hierarchy check
        if not hierarchy_check(ctx.author, member, ctx.guild.owner):
            embed = create_embed(
                title="❌ " + get_text(self.bot.languages, lang, 'errors.hierarchy_error'),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        old_nick = member.display_name
        await member.edit(nick=nickname, reason=f"Nickname changed by {ctx.author}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "NICKNAME", 
            f"Changed from '{old_nick}' to '{nickname or member.name}'"
        )
        
        # Send success message
        if nickname:
            embed = create_embed(
                title=f"✅ {member} kullanıcısının adı '{nickname}' olarak değiştirildi!",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title=f"✅ {member} kullanıcısının takma adı kaldırıldı!",
                color=discord.Color.green()
            )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(move_members=True)
    @commands.bot_has_permissions(move_members=True)
    async def voicekick(self, ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
        """Kick user from voice channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if not member.voice or not member.voice.channel:
            embed = create_embed(
                title="❌ Bu kullanıcı ses kanalında değil!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        channel_name = member.voice.channel.name
        await member.move_to(None, reason=f"{ctx.author}: {reason}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "VOICEKICK", f"{reason} (From: {channel_name})"
        )
        
        # Send success message
        embed = create_embed(
            title=f"🔊 {member} ses kanalından atıldı!",
            description=f"Kanal: {channel_name}\nSebep: {reason}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(move_members=True)
    @commands.bot_has_permissions(move_members=True)
    async def voicemove(self, ctx, member: discord.Member, channel: discord.VoiceChannel, *, reason="Sebep belirtilmedi"):
        """Move user to another voice channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if not member.voice or not member.voice.channel:
            embed = create_embed(
                title="❌ Bu kullanıcı ses kanalında değil!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        old_channel = member.voice.channel.name
        await member.move_to(channel, reason=f"{ctx.author}: {reason}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "VOICEMOVE", 
            f"{reason} (From: {old_channel} To: {channel.name})"
        )
        
        # Send success message
        embed = create_embed(
            title=f"🔊 {member} başka ses kanalına taşındı!",
            description=f"Eski kanal: {old_channel}\nYeni kanal: {channel.name}\nSebep: {reason}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['clearuser'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purgeuser(self, ctx, member: discord.Member, amount: int = 10):
        """Delete messages from a specific user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if amount < 1 or amount > 100:
            embed = create_embed(
                title="❌ Geçersiz miktar!",
                description="1-100 arası bir sayı girin.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        def check(message):
            return message.author == member
        
        deleted = await ctx.channel.purge(limit=amount*2, check=check)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "PURGEUSER", f"{len(deleted)} messages deleted"
        )
        
        # Send success message
        embed = create_embed(
            title=f"🗑️ {len(deleted)} mesaj silindi!",
            description=f"Kullanıcı: {member.mention}",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def giverole(self, ctx, member: discord.Member, *, role: discord.Role):
        """Give a role to a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if role in member.roles:
            embed = create_embed(
                title="❌ Bu kullanıcıda bu rol zaten var!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if role >= ctx.guild.me.top_role:
            embed = create_embed(
                title="❌ Bu rolü veremem! (Rol hiyerarşisi)",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await member.add_roles(role, reason=f"Role given by {ctx.author}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "ROLE_ADD", f"Added role: {role.name}"
        )
        
        # Send success message
        embed = create_embed(
            title=f"✅ {member} kullanıcısına {role.name} rolü verildi!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def takerole(self, ctx, member: discord.Member, *, role: discord.Role):
        """Remove a role from a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if role not in member.roles:
            embed = create_embed(
                title="❌ Bu kullanıcıda bu rol yok!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if role >= ctx.guild.me.top_role:
            embed = create_embed(
                title="❌ Bu rolü alamam! (Rol hiyerarşisi)",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "ROLE_REMOVE", f"Removed role: {role.name}"
        )
        
        # Send success message
        embed = create_embed(
            title=f"✅ {member} kullanıcısından {role.name} rolü alındı!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedModeration(bot))


    @commands.command(aliases=['clearbot'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clearbots(self, ctx, amount: int = 50):
        """Delete messages from bots."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if amount < 1 or amount > 100:
            embed = create_embed(
                title="❌ Geçersiz miktar!",
                description="1-100 arası bir sayı girin.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        def check(message):
            return message.author.bot
        
        deleted = await ctx.channel.purge(limit=amount*2, check=check)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "CLEARBOT", f"{len(deleted)} bot messages deleted"
        )
        
        # Send success message
        embed = create_embed(
            title=f"🤖 {len(deleted)} bot mesajı silindi!",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
    
    @commands.command(aliases=['clearlinks'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clearurls(self, ctx, amount: int = 50):
        """Delete messages containing links."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if amount < 1 or amount > 100:
            embed = create_embed(
                title="❌ Geçersiz miktar!",
                description="1-100 arası bir sayı girin.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        def check(message):
            import re
            link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            return bool(re.search(link_pattern, message.content))
        
        deleted = await ctx.channel.purge(limit=amount*2, check=check)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "CLEARLINKS", f"{len(deleted)} messages with links deleted"
        )
        
        # Send success message
        embed = create_embed(
            title=f"🔗 {len(deleted)} link içeren mesaj silindi!",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
    
    @commands.command(aliases=['clearinvites'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def cleardiscordinvites(self, ctx, amount: int = 50):
        """Delete messages containing Discord invites."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if amount < 1 or amount > 100:
            embed = create_embed(
                title="❌ Geçersiz miktar!",
                description="1-100 arası bir sayı girin.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        def check(message):
            import re
            invite_pattern = r'discord(?:\.gg|app\.com\/invite)\/[a-zA-Z0-9]+'
            return bool(re.search(invite_pattern, message.content))
        
        deleted = await ctx.channel.purge(limit=amount*2, check=check)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "CLEARINVITES", f"{len(deleted)} invite messages deleted"
        )
        
        # Send success message
        embed = create_embed(
            title=f"📨 {len(deleted)} davet içeren mesaj silindi!",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
    
    @commands.command(aliases=['clearembeds'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clearrich(self, ctx, amount: int = 50):
        """Delete messages with embeds."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if amount < 1 or amount > 100:
            embed = create_embed(
                title="❌ Geçersiz miktar!",
                description="1-100 arası bir sayı girin.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        def check(message):
            return len(message.embeds) > 0
        
        deleted = await ctx.channel.purge(limit=amount*2, check=check)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "CLEAREMBEDS", f"{len(deleted)} embed messages deleted"
        )
        
        # Send success message
        embed = create_embed(
            title=f"📎 {len(deleted)} embed içeren mesaj silindi!",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

