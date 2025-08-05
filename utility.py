import discord
from discord.ext import commands
from datetime import datetime
from utils.helpers import get_text
from utils.embeds import create_embed

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def userinfo(self, ctx, member=None):
        """Show user information."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        if member is None:
            member = ctx.author
        
        title_text = get_text(self.bot.languages, lang, 'commands.userinfo.title')
        id_text = get_text(self.bot.languages, lang, 'commands.userinfo.id')
        joined_server_text = get_text(self.bot.languages, lang, 'commands.userinfo.joined_server')
        joined_discord_text = get_text(self.bot.languages, lang, 'commands.userinfo.joined_discord')
        roles_text = get_text(self.bot.languages, lang, 'commands.userinfo.roles')
        status_text = get_text(self.bot.languages, lang, 'commands.userinfo.status')
        nickname_text = get_text(self.bot.languages, lang, 'commands.userinfo.nickname')
        
        embed = create_embed(
            title=title_text,
            color=member.color or discord.Color.blue()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name=id_text, value=member.id, inline=True)
        embed.add_field(name=status_text, value=str(member.status).title(), inline=True)
        embed.add_field(name=nickname_text, value=member.nick or "Yok", inline=True)
        
        # Join dates
        joined_server = member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Bilinmiyor"
        joined_discord = member.created_at.strftime("%d/%m/%Y")
        
        embed.add_field(name=joined_server_text, value=joined_server, inline=True)
        embed.add_field(name=joined_discord_text, value=joined_discord, inline=True)
        
        # Roles
        roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
        if roles:
            roles_value = " ".join(roles) if len(" ".join(roles)) < 1024 else f"{len(roles)} rol"
        else:
            roles_value = "Yok"
        
        embed.add_field(name=roles_text, value=roles_value, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def serverinfo(self, ctx):
        """Show server information."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        guild = ctx.guild
        
        title_text = get_text(self.bot.languages, lang, 'commands.serverinfo.title')
        owner_text = get_text(self.bot.languages, lang, 'commands.serverinfo.owner')
        created_text = get_text(self.bot.languages, lang, 'commands.serverinfo.created')
        members_text = get_text(self.bot.languages, lang, 'commands.serverinfo.members')
        channels_text = get_text(self.bot.languages, lang, 'commands.serverinfo.channels')
        roles_text = get_text(self.bot.languages, lang, 'commands.serverinfo.roles')
        boosts_text = get_text(self.bot.languages, lang, 'commands.serverinfo.boosts')
        
        embed = create_embed(
            title=f"{title_text} - {guild.name}",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name=owner_text, value=guild.owner.mention, inline=True)
        embed.add_field(name=created_text, value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        
        # Member counts
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        embed.add_field(name=members_text, value=f"👥 {guild.member_count}\n🟢 {online_members}", inline=True)
        
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        embed.add_field(name=channels_text, value=f"💬 {text_channels}\n🔊 {voice_channels}", inline=True)
        
        embed.add_field(name=roles_text, value=len(guild.roles), inline=True)
        embed.add_field(name=boosts_text, value=f"🚀 {guild.premium_subscription_count}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def avatar(self, ctx, member=None):
        """Show user avatar."""
        if member is None:
            member = ctx.author
        
        embed = create_embed(
            title=f"🖼️ {member.display_name} Avatarı",
            color=member.color or discord.Color.blue()
        )
        embed.set_image(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def ping(self, ctx):
        """Show bot latency."""
        embed = create_embed(
            title="🏓 Pong!",
            description=f"Gecikme: {round(self.bot.latency * 1000)}ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def help(self, ctx, category=None):
        """Show help menu."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        prefix = await self.bot.get_prefix(ctx.message)
        
        if isinstance(prefix, list):
            prefix = prefix[0]
        
        title_text = get_text(self.bot.languages, lang, 'commands.help.title')
        moderation_text = get_text(self.bot.languages, lang, 'commands.help.moderation')
        utility_text = get_text(self.bot.languages, lang, 'commands.help.utility')
        settings_text = get_text(self.bot.languages, lang, 'commands.help.settings')
        automod_text = get_text(self.bot.languages, lang, 'commands.help.automod')
        
        if not category:
            embed = create_embed(
                title=title_text,
                description=f"Komut öneki: `{prefix}`",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name=f"🛡️ {moderation_text}",
                value=f"`{prefix}help moderation`",
                inline=True
            )
            embed.add_field(
                name=f"🔧 {utility_text}",
                value=f"`{prefix}help utility`",
                inline=True
            )
            embed.add_field(
                name=f"⚙️ {settings_text}",
                value=f"`{prefix}help settings`",
                inline=True
            )
            embed.add_field(
                name=f"🤖 {automod_text}",
                value=f"`{prefix}help automod`",
                inline=True
            )
            embed.add_field(
                name="🎮 Eğlence",
                value=f"`{prefix}help fun`",
                inline=True
            )
            embed.add_field(
                name="💰 Ekonomi",
                value=f"`{prefix}help economy`",
                inline=True
            )
            embed.add_field(
                name="🎵 Müzik",
                value=f"`{prefix}help music`",
                inline=True
            )
            
        elif category.lower() == "moderation":
            embed = create_embed(
                title=f"🛡️ {moderation_text}",
                color=discord.Color.red()
            )
            
            commands_list = [
                f"`{prefix}ban [@kullanıcı] [sebep]` - Kullanıcıyı yasaklar",
                f"`{prefix}unban [kullanıcı_id] [sebep]` - Yasağı kaldırır", 
                f"`{prefix}kick [@kullanıcı] [sebep]` - Kullanıcıyı atar",
                f"`{prefix}mute [@kullanıcı] [süre] [sebep]` - Susturur",
                f"`{prefix}unmute [@kullanıcı]` - Susturmayı kaldırır",
                f"`{prefix}warn [@kullanıcı] [sebep]` - Uyarı verir",
                f"`{prefix}warnings [@kullanıcı]` - Uyarıları gösterir",
                f"`{prefix}clearwarns [@kullanıcı]` - Uyarıları temizler",
                f"`{prefix}lock [#kanal]` - Kanalı kilitler",
                f"`{prefix}unlock [#kanal]` - Kanal kilidini açar",
                f"`{prefix}purge [sayı]` - Mesaj siler",
                f"`{prefix}slowmode [saniye]` - Yavaş mod ayarlar"
            ]
            
            embed.description = "\n".join(commands_list)
            
        elif category.lower() == "utility":
            embed = create_embed(
                title=f"🔧 {utility_text}",
                color=discord.Color.green()
            )
            
            commands_list = [
                f"`{prefix}userinfo [@kullanıcı]` - Kullanıcı bilgisi",
                f"`{prefix}serverinfo` - Sunucu bilgisi",
                f"`{prefix}avatar [@kullanıcı]` - Avatar gösterir",
                f"`{prefix}ping` - Bot gecikmesi"
            ]
            
            embed.description = "\n".join(commands_list)
            
        elif category.lower() == "settings":
            embed = create_embed(
                title=f"⚙️ {settings_text}",
                color=discord.Color.orange()
            )
            
            commands_list = [
                f"`{prefix}setlang [tr/en]` - Dil ayarlar",
                f"`{prefix}setprefix [prefix]` - Komut öneki ayarlar",
                f"`{prefix}setwelcome [#kanal]` - Karşılama kanalı",
                f"`{prefix}setlog [#kanal]` - Log kanalı",
                f"`{prefix}setmuterole [@rol]` - Susturma rolü"
            ]
            
            embed.description = "\n".join(commands_list)
            
        elif category.lower() == "automod":
            embed = create_embed(
                title=f"🤖 {automod_text}",
                color=discord.Color.purple()
            )
            
            commands_list = [
                f"`{prefix}antispam [aç/kapat]` - Spam koruması",
                f"`{prefix}antilink [aç/kapat]` - Link engelleme",
                f"`{prefix}antiinvite [aç/kapat]` - Davet engelleme",
                f"`{prefix}blacklist [add/remove] [kelime]` - Kara liste",
                f"`{prefix}automod` - Otomatik moderasyon ayarları"
            ]
            
            embed.description = "\n".join(commands_list)
            
        elif category.lower() == "fun":
            embed = create_embed(
                title="🎮 Eğlence Komutları",
                color=discord.Color.purple()
            )
            
            commands_list = [
                f"`{prefix}8ball [soru]` - Sihirli 8 top",
                f"`{prefix}coinflip` - Para atma",
                f"`{prefix}dice [yüz]` - Zar atma",
                f"`{prefix}poll [soru]` - Anket oluşturma",
                f"`{prefix}choose [seçenek1, seçenek2]` - Rastgele seçim",
                f"`{prefix}rps [taş/kağıt/makas]` - Taş kağıt makas"
            ]
            
            embed.description = "\n".join(commands_list)
            
        elif category.lower() == "economy":
            embed = create_embed(
                title="💰 Ekonomi Komutları",
                color=discord.Color.gold()
            )
            
            commands_list = [
                f"`{prefix}balance [@kullanıcı]` - Bakiye görüntüleme",
                f"`{prefix}daily` - Günlük ödül alma",
                f"`{prefix}gamble [miktar]` - Kumar oynama",
                f"`{prefix}leaderboard` - Zenginlik sıralaması"
            ]
            
            embed.description = "\n".join(commands_list)
            
        elif category.lower() == "music":
            embed = create_embed(
                title="🎵 Müzik Komutları",
                color=discord.Color.blurple()
            )
            
            commands_list = [
                f"`{prefix}join` - Ses kanalına katılma",
                f"`{prefix}leave` - Ses kanalından ayrılma",
                f"`{prefix}volume [0-100]` - Ses seviyesi ayarlama",
                f"`{prefix}pause` - Müziği duraklatma",
                f"`{prefix}resume` - Müziği devam ettirme",
                f"`{prefix}stop` - Müziği durdurma"
            ]
            
            embed.description = "\n".join(commands_list)
        
        else:
            embed = create_embed(
                title="❌ Geçersiz kategori!",
                description="Geçerli kategoriler: `moderation`, `utility`, `settings`, `automod`, `fun`, `economy`, `music`",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
