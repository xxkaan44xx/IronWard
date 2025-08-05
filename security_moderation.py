
import discord
from discord.ext import commands
import asyncio
import re
from datetime import datetime, timedelta
from utils.embeds import create_embed
from utils.permissions import hierarchy_check
from utils.helpers import get_text, parse_time

class SecurityModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_protection = {}
        self.lockdown_channels = {}
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_guild=True)
    async def lockdown(self, ctx, *, reason="Güvenlik nedeniyle"):
        """Sunucuyu tamamen kilitle."""
        guild = ctx.guild
        locked_channels = []
        
        embed = create_embed(
            title="🔒 Sunucu kilitleniyor...",
            description="Tüm kanallar kilitleniyor, lütfen bekleyin...",
            color=discord.Color.red()
        )
        status_msg = await ctx.send(embed=embed)
        
        # Tüm metin kanallarını kilitle
        for channel in guild.text_channels:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                if overwrite.send_messages is not False:
                    overwrite.send_messages = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=f"Lockdown by {ctx.author}")
                    locked_channels.append(channel.id)
            except discord.Forbidden:
                continue
        
        # Ses kanallarını kilitle
        for channel in guild.voice_channels:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                if overwrite.connect is not False:
                    overwrite.connect = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=f"Lockdown by {ctx.author}")
                    locked_channels.append(channel.id)
            except discord.Forbidden:
                continue
        
        # Kilitli kanalları kaydet
        self.lockdown_channels[guild.id] = locked_channels
        
        # Log the action
        await self.bot.db.add_mod_log(
            guild.id, ctx.author.id, 0, "LOCKDOWN", f"Server locked: {reason}"
        )
        
        embed = create_embed(
            title="🔒 Sunucu kilitlendi!",
            description=f"**Sebep:** {reason}\n**Kilitli kanal sayısı:** {len(locked_channels)}",
            color=discord.Color.red()
        )
        await status_msg.edit(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_guild=True)
    async def unlockdown(self, ctx):
        """Sunucu kilitlemeyi kaldır."""
        guild = ctx.guild
        
        if guild.id not in self.lockdown_channels:
            embed = create_embed(
                title="❌ Sunucu zaten kilitli değil!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        locked_channels = self.lockdown_channels[guild.id]
        unlocked_count = 0
        
        embed = create_embed(
            title="🔓 Sunucu kilidi açılıyor...",
            description="Kanalların kilidi açılıyor, lütfen bekleyin...",
            color=discord.Color.green()
        )
        status_msg = await ctx.send(embed=embed)
        
        # Kilitli kanalların kilidini aç
        for channel_id in locked_channels:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    overwrite = channel.overwrites_for(guild.default_role)
                    if isinstance(channel, discord.TextChannel):
                        overwrite.send_messages = None
                    elif isinstance(channel, discord.VoiceChannel):
                        overwrite.connect = None
                    
                    await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=f"Unlockdown by {ctx.author}")
                    unlocked_count += 1
                except discord.Forbidden:
                    continue
        
        # Lockdown listesinden çıkar
        del self.lockdown_channels[guild.id]
        
        # Log the action
        await self.bot.db.add_mod_log(
            guild.id, ctx.author.id, 0, "UNLOCKDOWN", f"Server unlocked - {unlocked_count} channels"
        )
        
        embed = create_embed(
            title="🔓 Sunucu kilidi açıldı!",
            description=f"**Açılan kanal sayısı:** {unlocked_count}",
            color=discord.Color.green()
        )
        await status_msg.edit(embed=embed)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx, *, user_ids):
        """Toplu yasaklama (ID'lerle)."""
        user_id_list = []
        
        # ID'leri parse et
        for word in user_ids.split():
            try:
                user_id = int(word)
                user_id_list.append(user_id)
            except ValueError:
                continue
        
        if not user_id_list:
            embed = create_embed(
                title="❌ Geçerli kullanıcı ID'si bulunamadı!",
                description="Örnek: `!massban 123456789 987654321 111222333`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Onay mesajı
        embed = create_embed(
            title="⚠️ Toplu Yasaklama Onayı",
            description=f"**{len(user_id_list)} kullanıcı** yasaklanacak.\n\n**Bu işlemi onaylıyor musunuz?**",
            color=discord.Color.orange()
        )
        
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = create_embed(
                    title="❌ İşlem iptal edildi!",
                    color=discord.Color.gray()
                )
                await confirm_msg.edit(embed=embed)
                return
            
        except asyncio.TimeoutError:
            embed = create_embed(
                title="⏰ Zaman aşımı!",
                color=discord.Color.gray()
            )
            await confirm_msg.edit(embed=embed)
            return
        
        # Toplu yasaklama işlemi
        banned_count = 0
        failed_count = 0
        
        embed = create_embed(
            title="⏳ Toplu yasaklama başlatıldı...",
            description=f"İşlem devam ediyor... 0/{len(user_id_list)}",
            color=discord.Color.blue()
        )
        await confirm_msg.edit(embed=embed)
        
        for i, user_id in enumerate(user_id_list):
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.ban(user, reason=f"Mass ban by {ctx.author}")
                banned_count += 1
                
                # Log each ban
                await self.bot.db.add_mod_log(
                    ctx.guild.id, ctx.author.id, user_id, "MASSBAN", f"Mass ban operation"
                )
                
                # Update progress every 5 bans
                if (i + 1) % 5 == 0:
                    embed.description = f"İşlem devam ediyor... {i + 1}/{len(user_id_list)}"
                    await confirm_msg.edit(embed=embed)
                
                # Rate limit protection
                await asyncio.sleep(1)
                
            except Exception:
                failed_count += 1
        
        # Final result
        embed = create_embed(
            title="✅ Toplu yasaklama tamamlandı!",
            description=f"**Başarılı:** {banned_count}\n**Başarısız:** {failed_count}\n**Toplam:** {len(user_id_list)}",
            color=discord.Color.green()
        )
        await confirm_msg.edit(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Kanalı tamamen temizle (klonlayarak)."""
        if channel is None:
            channel = ctx.channel
        
        # Onay mesajı
        embed = create_embed(
            title="💥 Kanal Nuke Onayı",
            description=f"**{channel.name}** kanalı tamamen temizlenecek!\n\n**Bu işlem geri alınamaz. Onaylıyor musunuz?**",
            color=discord.Color.red()
        )
        
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = create_embed(
                    title="❌ İşlem iptal edildi!",
                    color=discord.Color.gray()
                )
                await confirm_msg.edit(embed=embed)
                return
            
        except asyncio.TimeoutError:
            embed = create_embed(
                title="⏰ Zaman aşımı!",
                color=discord.Color.gray()
            )
            await confirm_msg.edit(embed=embed)
            return
        
        # Kanal bilgilerini kaydet
        position = channel.position
        category = channel.category
        
        # Kanalı klonla ve eskisini sil
        new_channel = await channel.clone(reason=f"Nuked by {ctx.author}")
        await new_channel.edit(position=position)
        await channel.delete(reason=f"Nuked by {ctx.author}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "NUKE", f"Channel {channel.name} nuked"
        )
        
        # Başarı mesajı
        embed = create_embed(
            title="💥 Kanal temizlendi!",
            description=f"**{new_channel.name}** kanalı başarıyla temizlendi.",
            color=discord.Color.green()
        )
        await new_channel.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purgelinks(self, ctx, amount: int = 50):
        """Link içeren mesajları sil."""
        if amount > 100:
            amount = 100
        
        def has_link(message):
            link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            return re.search(link_pattern, message.content)
        
        deleted = await ctx.channel.purge(limit=amount, check=has_link)
        
        embed = create_embed(
            title=f"🔗 {len(deleted)} link mesajı silindi!",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "PURGELINKS", f"{len(deleted)} link messages deleted"
        )
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purgeimages(self, ctx, amount: int = 50):
        """Resim/dosya içeren mesajları sil."""
        if amount > 100:
            amount = 100
        
        def has_attachment(message):
            return len(message.attachments) > 0 or len(message.embeds) > 0
        
        deleted = await ctx.channel.purge(limit=amount, check=has_attachment)
        
        embed = create_embed(
            title=f"🖼️ {len(deleted)} resim/dosya mesajı silindi!",
            color=discord.Color.green()
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "PURGEIMAGES", f"{len(deleted)} image messages deleted"
        )
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def hackban(self, ctx, user_id: int, *, reason="Sebep belirtilmedi"):
        """Sunucuda olmayan kullanıcıyı yasakla."""
        try:
            user = await self.bot.fetch_user(user_id)
            
            # Kullanıcı sunucuda mı kontrol et
            member = ctx.guild.get_member(user_id)
            if member:
                embed = create_embed(
                    title="❌ Bu kullanıcı zaten sunucuda!",
                    description="Normal ban komutunu kullanın.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            # Hackban uygula
            await ctx.guild.ban(user, reason=f"{ctx.author}: {reason} (Hackban)")
            
            # Log the action
            await self.bot.db.add_mod_log(
                ctx.guild.id, ctx.author.id, user_id, "HACKBAN", reason
            )
            
            embed = create_embed(
                title=f"🔨 {user} hackban edildi!",
                description=f"**Sebep:** {reason}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            embed = create_embed(
                title="❌ Kullanıcı bulunamadı!",
                description="Geçersiz kullanıcı ID'si.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, toggle: str = None):
        """Anti-raid korumasını aç/kapat."""
        if toggle is None:
            # Mevcut durumu göster
            status = self.raid_protection.get(ctx.guild.id, False)
            embed = create_embed(
                title="🛡️ Anti-Raid Durumu",
                description=f"Anti-raid koruması: {'🟢 Açık' if status else '🔴 Kapalı'}",
                color=discord.Color.green() if status else discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if toggle.lower() in ['aç', 'on', 'enable', 'açık']:
            self.raid_protection[ctx.guild.id] = True
            embed = create_embed(
                title="🛡️ Anti-raid açıldı!",
                description="Şüpheli aktiviteler izlenecek.",
                color=discord.Color.green()
            )
        elif toggle.lower() in ['kapat', 'off', 'disable', 'kapalı']:
            self.raid_protection[ctx.guild.id] = False
            embed = create_embed(
                title="🛡️ Anti-raid kapatıldı!",
                color=discord.Color.red()
            )
        else:
            embed = create_embed(
                title="❌ Geçersiz seçenek!",
                description="Kullanım: `!antiraid [aç/kapat]`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Anti-raid koruması - yeni üye kontrolü."""
        guild = member.guild
        
        if guild.id not in self.raid_protection or not self.raid_protection[guild.id]:
            return
        
        # Hesap yaşı kontrolü (7 günden eski mi?)
        account_age = (datetime.now() - member.created_at).days
        
        if account_age < 7:
            try:
                # Şüpheli hesap - kick
                await member.kick(reason="Anti-raid: Account too new")
                
                # Log the action
                await self.bot.db.add_mod_log(
                    guild.id, self.bot.user.id, member.id, "ANTIRAID_KICK", 
                    f"Account age: {account_age} days"
                )
                
                # Admin bilgilendir
                settings = await self.bot.db.get_guild_settings(guild.id)
                if settings and settings['log_channel']:
                    log_channel = guild.get_channel(settings['log_channel'])
                    if log_channel:
                        embed = create_embed(
                            title="🛡️ Anti-Raid Aktivitesi",
                            description=f"**{member}** atıldı\n**Sebep:** Hesap çok yeni ({account_age} gün)",
                            color=discord.Color.orange()
                        )
                        await log_channel.send(embed=embed)
                        
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(SecurityModeration(bot))
