import discord
from discord.ext import commands
import random
import asyncio
from utils.embeds import create_embed

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['8ball'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def eightball(self, ctx, *, question):
        """8ball command."""
        responses = [
            "✅ Evet, kesinlikle!",
            "✅ Evet!",
            "🤔 Belki...",
            "❌ Hayır.",
            "❌ Kesinlikle hayır!",
            "🔮 Daha sonra tekrar sor.",
            "💭 Şüpheliyim...",
            "✨ Görünüyor ki evet!",
            "⚠️ Pek sanmıyorum.",
            "🎯 Kesinlikle!"
        ]

        response = random.choice(responses)

        embed = create_embed(
            title="🎱 8Ball",
            description=f"**Soru:** {question}\n**Cevap:** {response}",
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Soran: {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def coinflip(self, ctx):
        """Flip a coin."""
        result = random.choice(["Yazı", "Tura"])

        embed = create_embed(
            title="🪙 Yazı Tura",
            description=f"Sonuç: **{result}**",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dice(self, ctx, sides: int = 6):
        """Roll a dice."""
        if sides < 2 or sides > 100:
            embed = create_embed(
                title="❌ Geçersiz zar!",
                description="2-100 arası bir sayı girin.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        result = random.randint(1, sides)

        embed = create_embed(
            title="🎲 Zar Atma",
            description=f"🎲 **{result}** geldi! (1-{sides})",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def poll(self, ctx, *, question):
        """Create a simple yes/no poll."""
        embed = create_embed(
            title="📊 Anket",
            description=question,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Anketi başlatan: {ctx.author.display_name}")

        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rps(self, ctx, choice):
        """Rock Paper Scissors game."""
        choices = {
            "rock": "🗿",
            "paper": "📄", 
            "scissors": "✂️",
            "taş": "🗿",
            "kağıt": "📄",
            "makas": "✂️"
        }

        choice = choice.lower()
        if choice not in choices:
            embed = create_embed(
                title="❌ Geçersiz seçim!",
                description="Seçenekler: rock/taş, paper/kağıt, scissors/makas",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        bot_choice = random.choice(list(choices.keys())[:3])
        user_choice = choice if choice in ["rock", "paper", "scissors"] else {"taş": "rock", "kağıt": "paper", "makas": "scissors"}[choice]

        # Determine winner
        if user_choice == bot_choice:
            result = "🤝 Berabere!"
            col = discord.Color.orange()
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "🎉 Kazandın!"
            col = discord.Color.green()
        else:
            result = "😔 Kaybettin!"
            col = discord.Color.red()

        embed = create_embed(
            title="✂️ Taş Kağıt Makas",
            description=f"**Sen:** {choices[choice]}\n**Ben:** {choices[bot_choice]}\n\n**Sonuç:** {result}",
            color=col
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCommands(bot))