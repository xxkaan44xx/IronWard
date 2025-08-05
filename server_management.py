import discord
from discord.ext import commands
from datetime import datetime
from utils.embeds import create_embed
from utils.helpers import get_text

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=['sinfo', 'guildinfo'])
    async def sunucubilgi(self, ctx):
        """Show detailed server information."""
        guild = ctx.guild
        
        # Get server statistics
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = total_members - bot_count
        
        # Get channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Get role count
        role_count = len(guild.roles) - 1  # Exclude @everyone
        
        # Server features
        features = []
        if "VERIFIED" in guild.features:
            features.append("✅ Doğrulanmış")
        if "PARTNERED" in guild.features:
            features.append("🤝 Partner")
        if "VANITY_URL" in guild.features:
            features.append("🔗 Özel URL")
        if "BOOST_FEATURE" in guild.features:
            features.append("🚀 Boost")
        
        embed = create_embed(
            title=f"📊 {guild.name} Sunucu Bilgileri",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Basic info
        embed.add_field(name="📋 Temel Bilgiler", value=f"""
**Sahip:** {guild.owner.mention if guild.owner else "Bilinmiyor"}
**Sunucu ID:** {guild.id}
**Oluşturulma:** {guild.created_at.strftime('%d/%m/%Y')}
**Bölge:** {guild.preferred_locale}
**Doğrulama:** {guild.verification_level}
        """.strip(), inline=False)
        
        # Member statistics
        embed.add_field(name="👥 Üye İstatistikleri", value=f"""
**Toplam Üye:** {total_members:,}
**Çevrimiçi:** {online_members:,}
**İnsan:** {human_count:,}
**Bot:** {bot_count:,}
        """.strip(), inline=True)
        
        # Channel statistics
        embed.add_field(name="📺 Kanal İstatistikleri", value=f"""
**Metin Kanalı:** {text_channels}
**Ses Kanalı:** {voice_channels}
**Kategori:** {categories}
**Rol Sayısı:** {role_count}
        """.strip(), inline=True)
        
        # Boost info
        boost_info = f"""
**Boost Seviyesi:** {guild.premium_tier}
**Boost Sayısı:** {guild.premium_subscription_count or 0}
**Booster Sayısı:** {len(guild.premium_subscribers)}
        """.strip()
        embed.add_field(name="🚀 Boost Bilgileri", value=boost_info, inline=True)
        
        if features:
            embed.add_field(name="✨ Özellikler", value="\n".join(features), inline=False)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['boost'])
    async def boostbilgi(self, ctx):
        """Show server boost information."""
        guild = ctx.guild
        
        embed = create_embed(
            title=f"🚀 {guild.name} Boost Bilgileri",
            color=discord.Color.nitro_pink()
        )
        
        # Current boost status
        embed.add_field(name="📊 Mevcut Durum", value=f"""
**Seviye:** {guild.premium_tier}/3
**Toplam Boost:** {guild.premium_subscription_count or 0}
**Aktif Booster:** {len(guild.premium_subscribers)}
        """.strip(), inline=False)
        
        # Benefits by level
        benefits = {
            0: "• 8MB dosya boyutu\n• 50 emoji slotu",
            1: "• 8MB → 50MB dosya boyutu\n• 50 → 100 emoji slotu\n• Özel sunucu davet arkaplanı\n• 128kbps ses kalitesi",
            2: "• 50MB → 100MB dosya boyutu\n• 100 → 150 emoji slotu\n• Sunucu banner\n• 256kbps ses kalitesi",
            3: "• 100MB → 500MB dosya boyutu\n• 150 → 250 emoji slotu\n• Animasyonlu sunucu ikonu\n• Özel URL\n• 384kbps ses kalitesi"
        }
        
        current_benefits = benefits.get(guild.premium_tier, "Bilinmiyor")
        embed.add_field(name=f"✨ Seviye {guild.premium_tier} Avantajları", value=current_benefits, inline=False)
        
        # Next level requirements
        if guild.premium_tier < 3:
            required_boosts = {1: 2, 2: 7, 3: 14}
            next_level = guild.premium_tier + 1
            needed = required_boosts[next_level] - (guild.premium_subscription_count or 0)
            
            if needed > 0:
                embed.add_field(name=f"🎯 Seviye {next_level} için", value=f"**{needed} boost** daha gerekli!", inline=False)
            else:
                embed.add_field(name="🎉 Tebrikler!", value=f"Seviye {next_level} için yeterli boost var!", inline=False)
        else:
            embed.add_field(name="👑 Maksimum Seviye", value="Sunucu maksimum boost seviyesinde!", inline=False)
        
        # Top boosters
        if guild.premium_subscribers:
            boosters = guild.premium_subscribers[:10]  # Top 10
            booster_list = "\n".join([f"🚀 {member.display_name}" for member in boosters])
            embed.add_field(name="🏆 Boosterlar", value=booster_list, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['stats', 'sunucustat'])
    @commands.has_permissions(administrator=True)
    async def sunucuistatistik(self, ctx):
        """Show detailed server statistics."""
        guild = ctx.guild
        
        # Member join statistics (last 30 days approximation)
        now = datetime.now()
        recent_joins = sum(1 for member in guild.members 
                          if (now - member.joined_at).days <= 30 if member.joined_at)
        
        # Activity statistics
        active_members = sum(1 for member in guild.members 
                           if member.status != discord.Status.offline)
        
        embed = create_embed(
            title=f"📈 {guild.name} Detaylı İstatistikler",
            color=discord.Color.green()
        )
        
        # Member statistics
        embed.add_field(name="👥 Üye Analizi", value=f"""
**Toplam Üye:** {guild.member_count:,}
**Son 30 Gün Katılan:** {recent_joins}
**Aktif Üye:** {active_members}
**Çevrimdışı:** {guild.member_count - active_members}
        """.strip(), inline=True)
        
        # Channel activity
        embed.add_field(name="📺 Kanal Dağılımı", value=f"""
**Toplam Kanal:** {len(guild.channels)}
**Metin:** {len(guild.text_channels)}
**Ses:** {len(guild.voice_channels)}
**Kategori:** {len(guild.categories)}
**Forum:** {sum(1 for c in guild.channels if c.type == discord.ChannelType.forum)}
        """.strip(), inline=True)
        
        # Role statistics
        role_stats = {}
        for member in guild.members:
            role_count = len(member.roles) - 1  # Exclude @everyone
            role_stats[role_count] = role_stats.get(role_count, 0) + 1
        
        avg_roles = sum(len(member.roles) - 1 for member in guild.members) / guild.member_count
        
        embed.add_field(name="🎭 Rol İstatistikleri", value=f"""
**Toplam Rol:** {len(guild.roles) - 1}
**Ortalama Rol/Üye:** {avg_roles:.1f}
**En Çok Rol:** {max(role_stats.keys()) if role_stats else 0}
**Rolsüz Üye:** {role_stats.get(0, 0)}
        """.strip(), inline=True)
        
        # Server growth (approximation)
        old_members = sum(1 for member in guild.members 
                         if (now - member.joined_at).days > 30 if member.joined_at)
        growth_rate = (recent_joins / old_members * 100) if old_members > 0 else 0
        
        embed.add_field(name="📊 Büyüme Analizi", value=f"""
**Eski Üyeler:** {old_members}
**Yeni Üyeler:** {recent_joins}
**Büyüme Oranı:** {growth_rate:.1f}%
**Günlük Ortalama:** {recent_joins / 30:.1f}
        """.strip(), inline=True)
        
        # Voice channel usage
        voice_users = sum(len(vc.members) for vc in guild.voice_channels)
        embed.add_field(name="🔊 Ses Aktivitesi", value=f"""
**Ses Kanalındaki:** {voice_users}
**Boş Ses Kanalı:** {sum(1 for vc in guild.voice_channels if len(vc.members) == 0)}
**Dolu Ses Kanalı:** {sum(1 for vc in guild.voice_channels if len(vc.members) > 0)}
        """.strip(), inline=True)
        
        # Security statistics
        embed.add_field(name="🛡️ Güvenlik", value=f"""
**Doğrulama Seviyesi:** {guild.verification_level}
**2FA Gerekli:** {"Evet" if guild.mfa_level else "Hayır"}
**Açık DM:** {sum(1 for m in guild.members if not m.dm_channel)}
        """.strip(), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['uyesayisi', 'members'])
    @commands.has_permissions(manage_guild=True)
    async def uyecount(self, ctx):
        """Show member count with breakdown."""
        guild = ctx.guild
        
        # Count different member types
        humans = sum(1 for member in guild.members if not member.bot)
        bots = sum(1 for member in guild.members if member.bot)
        online = sum(1 for member in guild.members if member.status == discord.Status.online)
        idle = sum(1 for member in guild.members if member.status == discord.Status.idle)
        dnd = sum(1 for member in guild.members if member.status == discord.Status.dnd)
        offline = sum(1 for member in guild.members if member.status == discord.Status.offline)
        
        embed = create_embed(
            title=f"👥 {guild.name} Üye Sayısı",
            description=f"**Toplam Üye:** {guild.member_count:,}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="🧑‍🤝‍🧑 Üye Türü", value=f"""
**İnsan:** {humans:,}
**Bot:** {bots:,}
        """.strip(), inline=True)
        
        embed.add_field(name="🌐 Durum Dağılımı", value=f"""
🟢 **Çevrimiçi:** {online:,}
🟡 **Meşgul:** {idle:,}
🔴 **Rahatsız Etmeyin:** {dnd:,}
⚫ **Çevrimdışı:** {offline:,}
        """.strip(), inline=True)
        
        # Calculate percentages
        if guild.member_count > 0:
            online_percent = (online / guild.member_count) * 100
            bot_percent = (bots / guild.member_count) * 100
            
            embed.add_field(name="📊 Yüzdeler", value=f"""
**Çevrimiçi:** {online_percent:.1f}%
**Bot Oranı:** {bot_percent:.1f}%
**Aktiflik:** {((online + idle + dnd) / guild.member_count * 100):.1f}%
            """.strip(), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['emojis', 'emojistat'])
    @commands.has_permissions(administrator=True)
    async def emojiistatistik(self, ctx):
        """Show emoji usage statistics."""
        guild = ctx.guild
        
        if not guild.emojis:
            embed = create_embed(
                title="😔 Emoji bulunamadı!",
                description="Bu sunucuda özel emoji bulunmuyor.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Categorize emojis
        static_emojis = [e for e in guild.emojis if not e.animated]
        animated_emojis = [e for e in guild.emojis if e.animated]
        
        embed = create_embed(
            title=f"😀 {guild.name} Emoji İstatistikleri",
            color=discord.Color.gold()
        )
        
        # Basic stats
        embed.add_field(name="📊 Genel Bilgiler", value=f"""
**Toplam Emoji:** {len(guild.emojis)}
**Statik:** {len(static_emojis)}
**Animasyonlu:** {len(animated_emojis)}
**Emoji Limiti:** {guild.emoji_limit}
**Kalan Slot:** {guild.emoji_limit - len(guild.emojis)}
        """.strip(), inline=True)
        
        # Most recently added
        recent_emojis = sorted(guild.emojis, key=lambda e: e.created_at, reverse=True)[:5]
        if recent_emojis:
            recent_list = "\n".join([f"{emoji} `:{emoji.name}:`" for emoji in recent_emojis])
            embed.add_field(name="🆕 Son Eklenenler", value=recent_list, inline=True)
        
        # Largest emojis (by name length)
        long_name_emojis = sorted(guild.emojis, key=lambda e: len(e.name), reverse=True)[:5]
        if long_name_emojis:
            long_names = "\n".join([f"{emoji} `{len(emoji.name)} karakter`" for emoji in long_name_emojis])
            embed.add_field(name="📏 En Uzun İsimler", value=long_names, inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))