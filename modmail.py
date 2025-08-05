
import discord
from discord.ext import commands
import asyncio
from utils.embeds import create_embed

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def modmail(self, ctx, toggle: str = None):
        """Modmail sistemini aç/kapat."""
        if toggle is None:
            settings = await self.bot.db.get_guild_settings(ctx.guild.id)
            modmail_enabled = settings.get('modmail_enabled', False) if settings else False
            
            embed = create_embed(
                title="📬 ModMail Durumu",
                description=f"ModMail sistemi: {'🟢 Açık' if modmail_enabled else '🔴 Kapalı'}",
                color=discord.Color.green() if modmail_enabled else discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if toggle.lower() in ['aç', 'on', 'enable', 'açık']:
            await self.bot.db.update_guild_setting(ctx.guild.id, 'modmail_enabled', True)
            embed = create_embed(
                title="📬 ModMail açıldı!",
                description="Kullanıcılar artık bota DM göndererek destek talebinde bulunabilir.",
                color=discord.Color.green()
            )
        elif toggle.lower() in ['kapat', 'off', 'disable', 'kapalı']:
            await self.bot.db.update_guild_setting(ctx.guild.id, 'modmail_enabled', False)
            embed = create_embed(
                title="📬 ModMail kapatıldı!",
                color=discord.Color.red()
            )
        else:
            embed = create_embed(
                title="❌ Geçersiz seçenek!",
                description="Kullanım: `!modmail [aç/kapat]`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmodmail(self, ctx, channel: discord.TextChannel):
        """ModMail kanalını ayarla."""
        await self.bot.db.update_guild_setting(ctx.guild.id, 'modmail_channel', channel.id)
        
        embed = create_embed(
            title="📬 ModMail kanalı ayarlandı!",
            description=f"ModMail kanalı: {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """ModMail DM handler."""
        if message.author.bot or message.guild:
            return
        
        # Kullanıcının ortak sunucularını bul
        common_guilds = [guild for guild in self.bot.guilds if guild.get_member(message.author.id)]
        
        for guild in common_guilds:
            settings = await self.bot.db.get_guild_settings(guild.id)
            if not settings or not settings.get('modmail_enabled') or not settings.get('modmail_channel'):
                continue
            
            modmail_channel = guild.get_channel(settings['modmail_channel'])
            if not modmail_channel:
                continue
            
            # ModMail embed oluştur
            embed = create_embed(
                title="📬 Yeni ModMail Mesajı",
                description=message.content,
                color=discord.Color.blue()
            )
            embed.set_author(
                name=f"{message.author} ({message.author.id})",
                icon_url=message.author.display_avatar.url
            )
            embed.set_footer(text=f"Sunucu: {guild.name}")
            
            # Dosya varsa ekle
            files = []
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.size <= 8000000:  # 8MB limit
                        file_data = await attachment.read()
                        files.append(discord.File(file_data, attachment.filename))
            
            # Mesajı gönder
            await modmail_channel.send(embed=embed, files=files)
            
            # Kullanıcıya onay gönder
            embed = create_embed(
                title="✅ Mesajınız gönderildi!",
                description=f"**{guild.name}** sunucusunun moderatörlerine mesajınız iletildi.",
                color=discord.Color.green()
            )
            await message.author.send(embed=embed)
            break
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def reply(self, ctx, user_id: int, *, message):
        """ModMail'e cevap ver."""
        try:
            user = await self.bot.fetch_user(user_id)
            
            embed = create_embed(
                title=f"📬 {ctx.guild.name} - Moderatör Yanıtı",
                description=message,
                color=discord.Color.green()
            )
            embed.set_author(
                name=f"{ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            
            await user.send(embed=embed)
            
            # Kanala onay mesajı
            embed = create_embed(
                title="✅ Yanıt gönderildi!",
                description=f"**{user}** kullanıcısına yanıt gönderildi.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            embed = create_embed(
                title="❌ Kullanıcı bulunamadı!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = create_embed(
                title="❌ Kullanıcıya mesaj gönderilemedi!",
                description="Kullanıcı DM'lerini kapatmış olabilir.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModMail(bot))
