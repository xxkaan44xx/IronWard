
import discord
from discord.ext import commands
import asyncio
from utils.embeds import create_embed

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
    
    @commands.command()
    async def join(self, ctx):
        """Join voice channel."""
        if not ctx.author.voice:
            embed = create_embed(
                title="❌ Ses kanalında değilsin!",
                description="Önce bir ses kanalına katıl!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        channel = ctx.author.voice.channel
        
        if ctx.guild.id in self.voice_clients:
            await self.voice_clients[ctx.guild.id].move_to(channel)
        else:
            self.voice_clients[ctx.guild.id] = await channel.connect()
        
        embed = create_embed(
            title="🎵 Ses kanalına katıldım!",
            description=f"**{channel.name}** kanalına bağlandım!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def leave(self, ctx):
        """Leave voice channel."""
        if ctx.guild.id not in self.voice_clients:
            embed = create_embed(
                title="❌ Zaten ses kanalında değilim!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await self.voice_clients[ctx.guild.id].disconnect()
        del self.voice_clients[ctx.guild.id]
        
        if ctx.guild.id in self.queues:
            del self.queues[ctx.guild.id]
        
        embed = create_embed(
            title="👋 Ses kanalından ayrıldım!",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def volume(self, ctx, volume: int = None):
        """Set or check volume."""
        if ctx.guild.id not in self.voice_clients:
            embed = create_embed(
                title="❌ Ses kanalında değilim!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        voice_client = self.voice_clients[ctx.guild.id]
        
        if volume is None:
            current_vol = int(voice_client.source.volume * 100) if voice_client.source else 50
            embed = create_embed(
                title="🔊 Ses Seviyesi",
                description=f"Mevcut ses seviyesi: **{current_vol}%**",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        if volume < 0 or volume > 100:
            embed = create_embed(
                title="❌ Geçersiz ses seviyesi!",
                description="Ses seviyesi 0-100 arasında olmalı!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if voice_client.source:
            voice_client.source.volume = volume / 100
        
        embed = create_embed(
            title="🔊 Ses seviyesi ayarlandı!",
            description=f"Yeni ses seviyesi: **{volume}%**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def pause(self, ctx):
        """Pause music."""
        if ctx.guild.id not in self.voice_clients:
            embed = create_embed(
                title="❌ Ses kanalında değilim!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        voice_client = self.voice_clients[ctx.guild.id]
        
        if voice_client.is_playing():
            voice_client.pause()
            embed = create_embed(
                title="⏸️ Müzik duraklatıldı!",
                color=discord.Color.orange()
            )
        else:
            embed = create_embed(
                title="❌ Şu an müzik çalmıyor!",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def resume(self, ctx):
        """Resume music."""
        if ctx.guild.id not in self.voice_clients:
            embed = create_embed(
                title="❌ Ses kanalında değilim!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        voice_client = self.voice_clients[ctx.guild.id]
        
        if voice_client.is_paused():
            voice_client.resume()
            embed = create_embed(
                title="▶️ Müzik devam ediyor!",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Müzik zaten çalıyor!",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def stop(self, ctx):
        """Stop music."""
        if ctx.guild.id not in self.voice_clients:
            embed = create_embed(
                title="❌ Ses kanalında değilim!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        voice_client = self.voice_clients[ctx.guild.id]
        
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            embed = create_embed(
                title="⏹️ Müzik durduruldu!",
                color=discord.Color.red()
            )
        else:
            embed = create_embed(
                title="❌ Şu an müzik çalmıyor!",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
