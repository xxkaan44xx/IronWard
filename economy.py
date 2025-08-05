
import discord
from discord.ext import commands
import random
from utils.embeds import create_embed
from datetime import datetime, timedelta

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def get_balance(self, guild_id, user_id):
        """Get user balance."""
        async with self.bot.db.db_lock:
            cursor = self.bot.db.cursor
            cursor.execute(
                "SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    
    async def add_money(self, guild_id, user_id, amount):
        """Add money to user."""
        async with self.bot.db.db_lock:
            cursor = self.bot.db.cursor
            cursor.execute(
                "INSERT OR REPLACE INTO economy (guild_id, user_id, balance, last_daily) VALUES (?, ?, COALESCE((SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?), 0) + ?, COALESCE((SELECT last_daily FROM economy WHERE guild_id = ? AND user_id = ?), ''))",
                (guild_id, user_id, guild_id, user_id, amount, guild_id, user_id)
            )
            self.bot.db.conn.commit()
    
    async def check_daily(self, guild_id, user_id):
        """Check if user can claim daily."""
        async with self.bot.db.db_lock:
            cursor = self.bot.db.cursor
            cursor.execute(
                "SELECT last_daily FROM economy WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            result = cursor.fetchone()
            
            if not result or not result[0]:
                return True
            
            last_daily = datetime.fromisoformat(result[0])
            return datetime.now() > last_daily + timedelta(hours=24)
    
    async def set_daily(self, guild_id, user_id):
        """Set daily claim time."""
        async with self.bot.db.db_lock:
            cursor = self.bot.db.cursor
            cursor.execute(
                "INSERT OR REPLACE INTO economy (guild_id, user_id, balance, last_daily) VALUES (?, ?, COALESCE((SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?), 0), ?)",
                (guild_id, user_id, guild_id, user_id, datetime.now().isoformat())
            )
            self.bot.db.conn.commit()
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def balance(self, ctx, member: discord.Member = None):
        """Check balance."""
        target = member or ctx.author
        balance = await self.get_balance(ctx.guild.id, target.id)
        
        embed = create_embed(
            title="💰 Bakiye",
            description=f"**{target.display_name}** adlı kullanıcının bakiyesi: **{balance:,}** 🪙",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hours
    async def daily(self, ctx):
        """Claim daily coins."""
        if not await self.check_daily(ctx.guild.id, ctx.author.id):
            embed = create_embed(
                title="⏰ Günlük ödül zaten alındı!",
                description="24 saat sonra tekrar dene!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        amount = random.randint(100, 300)
        await self.add_money(ctx.guild.id, ctx.author.id, amount)
        await self.set_daily(ctx.guild.id, ctx.author.id)
        
        embed = create_embed(
            title="🎁 Günlük Ödül",
            description=f"**{amount:,}** 🪙 kazandın!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gamble(self, ctx, amount: int):
        """Gamble coins."""
        if amount < 10:
            embed = create_embed(
                title="❌ Minimum bahis 10 🪙!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        balance = await self.get_balance(ctx.guild.id, ctx.author.id)
        
        if balance < amount:
            embed = create_embed(
                title="❌ Yetersiz bakiye!",
                description=f"Bakiyeniz: **{balance:,}** 🪙",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # 45% win chance
        if random.randint(1, 100) <= 45:
            winnings = amount * random.uniform(1.5, 2.5)
            await self.add_money(ctx.guild.id, ctx.author.id, int(winnings) - amount)
            
            embed = create_embed(
                title="🎉 Kazandın!",
                description=f"**{int(winnings):,}** 🪙 kazandın!",
                color=discord.Color.green()
            )
        else:
            await self.add_money(ctx.guild.id, ctx.author.id, -amount)
            
            embed = create_embed(
                title="😔 Kaybettin!",
                description=f"**{amount:,}** 🪙 kaybettin!",
                color=discord.Color.red()
            )
        
        new_balance = await self.get_balance(ctx.guild.id, ctx.author.id)
        embed.add_field(name="Yeni Bakiye", value=f"{new_balance:,} 🪙", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leaderboard(self, ctx):
        """Show economy leaderboard."""
        async with self.bot.db.db_lock:
            cursor = self.bot.db.cursor
            cursor.execute(
                "SELECT user_id, balance FROM economy WHERE guild_id = ? ORDER BY balance DESC LIMIT 10",
                (ctx.guild.id,)
            )
            results = cursor.fetchall()
        
        if not results:
            embed = create_embed(
                title="📊 Zenginlik Sıralaması",
                description="Henüz kimse para kazanmamış!",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        description = ""
        for i, (user_id, balance) in enumerate(results, 1):
            user = self.bot.get_user(user_id)
            name = user.display_name if user else f"Bilinmeyen Kullanıcı ({user_id})"
            
            if i == 1:
                emoji = "🥇"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"
            else:
                emoji = f"{i}."
            
            description += f"{emoji} **{name}** - {balance:,} 🪙\n"
        
        embed = create_embed(
            title="📊 Zenginlik Sıralaması",
            description=description,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
