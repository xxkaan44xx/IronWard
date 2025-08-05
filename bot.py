import discord
from discord.ext import commands
import asyncio
import json
import logging
from database import Database
from utils.helpers import get_text
from utils.embeds import create_embed

# Configure logging
logging.basicConfig(level=logging.INFO)

class IronWardBot(commands.Bot):
    """IronWard - Advanced Discord Moderation Bot"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        intents.voice_states = True

        super().__init__(
            command_prefix="!",  # Default prefix, will be overridden per guild
            intents=intents,
            help_command=None,
            case_insensitive=True
        )

        self.db = Database()
        self.languages = {}

    async def setup_hook(self):
        """Called when the bot is starting up."""
        # Load language files
        await self.load_languages()

        # Load all cogs
        await self.load_cogs()

        # Initialize database
        await self.db.init_db()

        print("✅ Bot kurulumu tamamlandı!")

    async def load_languages(self):
        """Load language files."""
        try:
            with open('languages/tr.json', 'r', encoding='utf-8') as f:
                self.languages['tr'] = json.load(f)

            with open('languages/en.json', 'r', encoding='utf-8') as f:
                self.languages['en'] = json.load(f)

            print("✅ Dil dosyaları yüklendi!")
        except Exception as e:
            print(f"❌ Dil dosyaları yüklenirken hata: {e}")

    async def load_cogs(self):
        """Load all bot cogs."""
        cogs = [
            'cogs.moderation',
            'cogs.utility',
            'cogs.settings',
            'cogs.automod',
            'cogs.advanced_moderation',
            'cogs.logging',
            'cogs.channel_management',
            'cogs.role_management',
            'cogs.server_management',
            'cogs.ticket_system',
            'cogs.reaction_roles',
            'cogs.fun_commands',
            'cogs.security_moderation',
            'cogs.modmail',
            'cogs.ai_assistant'
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ {cog} yüklendi!")
            except Exception as e:
                print(f"❌ {cog} yüklenirken hata: {e}")

    async def get_prefix(self, message):
        """Get command prefix for guild."""
        if not message.guild:
            return "!"

        prefix = await self.db.get_prefix(message.guild.id)
        return prefix or "!"

    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"🤖 IronWard ({self.user}) başarıyla başlatıldı!")
        print(f"📊 {len(self.guilds)} sunucuda aktif koruma sağlıyor")
        
        for guild in self.guilds:
            print(f"   - {guild.name} ({guild.id}) - {guild.member_count or 0} üye")
        
        total_members = sum(guild.member_count or 0 for guild in self.guilds)
        print(f"👥 {total_members} kullanıcıyı koruyor")
        print("=" * 50)
        print("✅ Bot Discord'da AKTIF ve hazır!")

        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.watching, name="!help | IronWard Moderasyon Botu")
        await self.change_presence(activity=activity)

    async def on_guild_join(self, guild):
        """Called when bot joins a new guild."""
        # Create language selection embed
        lang = await self.db.get_language(guild.id) or 'tr'

        embed = create_embed(
            title="🌍 Dil Seçimi / Language Selection",
            description=(
                "**Türkçe:** Merhaba! Bu sunucuda kullanılacak dili seçin.\n"
                "**English:** Hello! Please select the language for this server.\n\n"
                "🇹🇷 Türkçe için: `!setlang tr`\n"
                "🇬🇧 English için: `!setlang en`"
            ),
            color=discord.Color.blue()
        )

        # Try to send to system channel or first available text channel
        channel = guild.system_channel
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break

        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    async def on_command_error(self, ctx, error):
        """Global error handler."""
        lang = await self.db.get_language(ctx.guild.id) if ctx.guild else 'tr'

        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.MissingPermissions):
            embed = create_embed(
                title="❌ " + get_text(self.languages, lang, 'errors.no_permission'),
                description=get_text(self.languages, lang, 'errors.missing_permissions'),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BotMissingPermissions):
            embed = create_embed(
                title="❌ " + get_text(self.languages, lang, 'errors.bot_no_permission'),
                description=get_text(self.languages, lang, 'errors.bot_missing_permissions'),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MemberNotFound):
            embed = create_embed(
                title="❌ " + get_text(self.languages, lang, 'errors.member_not_found'),
                description=get_text(self.languages, lang, 'errors.member_not_found_desc'),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = create_embed(
                title="⏰ " + get_text(self.languages, lang, 'errors.cooldown'),
                description=get_text(self.languages, lang, 'errors.cooldown_desc').format(error.retry_after),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

        else:
            embed = create_embed(
                title="❌ " + get_text(self.languages, lang, 'errors.unknown'),
                description=f"```{str(error)}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"Unhandled error: {error}")