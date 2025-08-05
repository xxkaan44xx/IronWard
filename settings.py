import discord
from discord.ext import commands
from utils.helpers import get_text
from utils.embeds import create_embed

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlang(self, ctx, language: str):
        """Set server language."""
        if language.lower() not in ['tr', 'en']:
            embed = create_embed(
                title="❌ Geçersiz dil!",
                description="Geçerli diller: `tr` (Türkçe), `en` (English)",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await self.bot.db.set_language(ctx.guild.id, language.lower())
        
        if language.lower() == 'tr':
            text = "✅ Sunucu dili **Türkçe** olarak ayarlandı!"
        else:
            text = "✅ Server language set to **English**!"
        
        embed = create_embed(
            title=text,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        """Set command prefix."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if len(prefix) > 5:
            embed = create_embed(
                title="❌ Çok uzun prefix!",
                description="Prefix en fazla 5 karakter olabilir.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await self.bot.db.set_prefix(ctx.guild.id, prefix)
        
        success_text = get_text(self.bot.languages, lang, 'settings.prefix_set')
        embed = create_embed(
            title=success_text.format(prefix=prefix),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel):
        """Set welcome channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        await self.bot.db.update_guild_setting(ctx.guild.id, 'welcome_channel', channel.id)
        
        success_text = get_text(self.bot.languages, lang, 'settings.welcome_channel_set')
        embed = create_embed(
            title=success_text.format(channel=channel.mention),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        """Set log channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        await self.bot.db.update_guild_setting(ctx.guild.id, 'log_channel', channel.id)
        
        success_text = get_text(self.bot.languages, lang, 'settings.log_channel_set')
        embed = create_embed(
            title=success_text.format(channel=channel.mention),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmuterole(self, ctx, role: discord.Role):
        """Set mute role."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        await self.bot.db.update_guild_setting(ctx.guild.id, 'mute_role', role.id)
        
        success_text = get_text(self.bot.languages, lang, 'settings.mute_role_set')
        embed = create_embed(
            title=success_text.format(role=role.mention),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setautorole(self, ctx, role: discord.Role):
        """Set auto role for new members."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        await self.bot.db.update_guild_setting(ctx.guild.id, 'auto_role', role.id)
        
        embed = create_embed(
            title=f"✅ Otomatik rol {role.mention} olarak ayarlandı!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Show current server settings."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        prefix = await self.bot.get_prefix(ctx.message)
        
        if isinstance(prefix, list):
            prefix = prefix[0]
        
        embed = create_embed(
            title="⚙️ Sunucu Ayarları",
            color=discord.Color.blue()
        )
        
        # Language
        lang_display = "🇹🇷 Türkçe" if lang == 'tr' else "🇬🇧 English"
        embed.add_field(name="🌍 Dil", value=lang_display, inline=True)
        
        # Prefix
        embed.add_field(name="💬 Komut Öneki", value=f"`{prefix}`", inline=True)
        
        if settings:
            # Welcome Channel
            welcome_ch = ctx.guild.get_channel(settings['welcome_channel']) if settings['welcome_channel'] else None
            embed.add_field(
                name="👋 Karşılama Kanalı", 
                value=welcome_ch.mention if welcome_ch else "Ayarlanmamış", 
                inline=True
            )
            
            # Log Channel
            log_ch = ctx.guild.get_channel(settings['log_channel']) if settings['log_channel'] else None
            embed.add_field(
                name="📝 Log Kanalı", 
                value=log_ch.mention if log_ch else "Ayarlanmamış", 
                inline=True
            )
            
            # Mute Role
            mute_role = ctx.guild.get_role(settings['mute_role']) if settings['mute_role'] else None
            embed.add_field(
                name="🔇 Susturma Rolü", 
                value=mute_role.mention if mute_role else "Ayarlanmamış", 
                inline=True
            )
            
            # Auto Role
            auto_role = ctx.guild.get_role(settings['auto_role']) if settings['auto_role'] else None
            embed.add_field(
                name="🎭 Otomatik Rol", 
                value=auto_role.mention if auto_role else "Ayarlanmamış", 
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
