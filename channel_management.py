import discord
from discord.ext import commands
from utils.embeds import create_embed
from utils.helpers import get_text

class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def hidechannel(self, ctx, channel=None):
        """Hide a channel from @everyone."""
        if channel is None:
            channel = ctx.channel

        # Remove read permissions from @everyone
        await channel.set_permissions(ctx.guild.default_role, read_messages=False)

        embed = create_embed(
            title=f"👁️‍🗨️ Kanal gizlendi!",
            description=f"{channel.mention} kanalı @everyone rolünden gizlendi.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def showchannel(self, ctx, channel=None):
        """Show a hidden channel to @everyone."""
        if channel is None:
            channel = ctx.channel

        # Restore read permissions to @everyone
        await channel.set_permissions(ctx.guild.default_role, read_messages=True)

        embed = create_embed(
            title=f"👁️ Kanal gösterildi!",
            description=f"{channel.mention} kanalı @everyone rolüne açıldı.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def renamechannel(self, ctx, channel, *, new_name):
        """Rename a channel."""
        old_name = channel.name
        await channel.edit(name=new_name, reason=f"Channel renamed by {ctx.author}")

        embed = create_embed(
            title="✏️ Kanal adı değiştirildi!",
            description=f"**Eski ad:** #{old_name}\n**Yeni ad:** #{new_name}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def createchannel(self, ctx, channel_type, *, name):
        """Create a new channel."""
        if channel_type.lower() in ['text', 'metin']:
            channel = await ctx.guild.create_text_channel(
                name, 
                reason=f"Text channel created by {ctx.author}"
            )
            embed = create_embed(
                title="✅ Metin kanalı oluşturuldu!",
                description=f"**Kanal:** {channel.mention}\n**Ad:** {name}",
                color=discord.Color.green()
            )
        elif channel_type.lower() in ['voice', 'ses']:
            channel = await ctx.guild.create_voice_channel(
                name, 
                reason=f"Voice channel created by {ctx.author}"
            )
            embed = create_embed(
                title="✅ Ses kanalı oluşturuldu!",
                description=f"**Kanal:** {channel.name}\n**Ad:** {name}",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Geçersiz kanal türü!",
                description="Geçerli türler: `text`, `metin`, `voice`, `ses`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def deletechannel(self, ctx, channel=None):
        """Delete a channel."""
        if channel is None:
            channel = ctx.channel

        if channel == ctx.channel:
            # If deleting current channel, send message to another channel
            embed = create_embed(
                title="🗑️ Kanal siliniyor...",
                description=f"#{channel.name} kanalı 5 saniye içinde silinecek!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

            import asyncio
            await asyncio.sleep(5)
            await channel.delete(reason=f"Channel deleted by {ctx.author}")
        else:
            channel_name = channel.name
            await channel.delete(reason=f"Channel deleted by {ctx.author}")

            embed = create_embed(
                title="🗑️ Kanal silindi!",
                description=f"#{channel_name} kanalı başarıyla silindi.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def clonechannel(self, ctx, channel=None):
        """Clone a channel."""
        if channel is None:
            channel = ctx.channel

        # Create clone
        cloned = await channel.clone(reason=f"Channel cloned by {ctx.author}")

        embed = create_embed(
            title="📋 Kanal kopyalandı!",
            description=f"**Orijinal:** {channel.mention}\n**Kopya:** {cloned.mention}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def pin(self, ctx, message_id: int):
        """Pin a message by ID."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.pin(reason=f"Message pinned by {ctx.author}")

            embed = create_embed(
                title="📌 Mesaj sabitlendi!",
                description=f"[Mesaj]({message.jump_url}) başarıyla sabitlendi.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except discord.NotFound:
            embed = create_embed(
                title="❌ Mesaj bulunamadı!",
                description="Belirtilen ID'ye sahip mesaj bu kanalda bulunamadı.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def unpin(self, ctx, message_id: int):
        """Unpin a message by ID."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.unpin(reason=f"Message unpinned by {ctx.author}")

            embed = create_embed(
                title="📌 Mesaj sabitleme kaldırıldı!",
                description=f"[Mesaj]({message.jump_url}) sabitlemesi kaldırıldı.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except discord.NotFound:
            embed = create_embed(
                title="❌ Mesaj bulunamadı!",
                description="Belirtilen ID'ye sahip mesaj bu kanalda bulunamadı.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def voicelock(self, ctx, channel):
        """Lock a voice channel."""
        # Remove connect permission from @everyone
        await channel.set_permissions(ctx.guild.default_role, connect=False)

        embed = create_embed(
            title="🔒 Ses kanalı kilitlendi!",
            description=f"**{channel.name}** ses kanalı kilitlendi.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def voiceunlock(self, ctx, channel):
        """Unlock a voice channel."""
        # Restore connect permission to @everyone
        await channel.set_permissions(ctx.guild.default_role, connect=None)

        embed = create_embed(
            title="🔓 Ses kanalı kilidi açıldı!",
            description=f"**{channel.name}** ses kanalının kilidi açıldı.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['clearmedia', 'clearfiles'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clearattachments(self, ctx, amount: int = 10):
        """Clear messages with attachments."""
        deleted_messages = await ctx.channel.purge(limit=amount, check=lambda m: m.attachments != [])

        embed = create_embed(
            title="🗑️ Ekli mesajlar temizlendi!",
            description=f"{len(deleted_messages)} mesaj (ekli) başarıyla silindi.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))