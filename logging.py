import discord
from discord.ext import commands
from datetime import datetime, timedelta
from utils.embeds import create_embed
from utils.helpers import get_text

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def modlogs(self, ctx, member: discord.Member = None, limit: int = 10):
        """Show moderation logs for a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)

        if limit > 50:
            limit = 50

        if member:
            logs = await self.bot.db.get_mod_logs_for_user(ctx.guild.id, member.id, limit)
            title = f"📋 {member} kullanıcısının moderasyon geçmişi"
        else:
            logs = await self.bot.db.get_mod_logs(ctx.guild.id, limit)
            title = "📋 Sunucu moderasyon geçmişi"

        if not logs:
            embed = create_embed(
                title="📋 Moderasyon geçmişi bulunamadı",
                description="Bu kullanıcı için herhangi bir moderasyon kaydı bulunamadı.",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)

        embed = create_embed(
            title=title,
            color=discord.Color.blue()
        )

        for log in logs:
            moderator = ctx.guild.get_member(log['moderator_id'])
            mod_name = moderator.display_name if moderator else "Bilinmiyor"

            target = ctx.guild.get_member(log['user_id'])
            target_name = target.display_name if target else f"ID: {log['user_id']}"

            timestamp = log['timestamp'][:16] if len(log['timestamp']) > 16 else log['timestamp']

            embed.add_field(
                name=f"{log['action']} - {timestamp}",
                value=f"**Hedef:** {target_name}\n**Moderatör:** {mod_name}\n**Sebep:** {log['reason']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def banlist(self, ctx):
        """Show banned users."""
        lang = await self.bot.db.get_language(ctx.guild.id)

        try:
            bans = [ban async for ban in ctx.guild.bans()]

            if not bans:
                embed = create_embed(
                    title="📋 Ban Listesi",
                    description="Bu sunucuda yasaklı kullanıcı bulunmuyor.",
                    color=discord.Color.green()
                )
                return await ctx.send(embed=embed)

            embed = create_embed(
                title=f"📋 Ban Listesi ({len(bans)} kullanıcı)",
                color=discord.Color.red()
            )

            ban_text = ""
            for i, ban in enumerate(bans[:20]):  # Limit to 20 bans
                reason = ban.reason or "Sebep belirtilmemiş"
                ban_text += f"{i+1}. **{ban.user}** - {reason}\n"

            if len(bans) > 20:
                ban_text += f"\n... ve {len(bans) - 20} kullanıcı daha"

            embed.description = ban_text
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = create_embed(
                title="❌ Hata",
                description="Ban listesini görüntülemek için yeterli iznim yok.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def report(self, ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
        """Report a user to moderators."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)

        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass

        # Send DM to reporter
        embed = create_embed(
            title="✅ Rapor gönderildi",
            description=f"**Raporlanan:** {member.mention}\n**Sebep:** {reason}",
            color=discord.Color.green()
        )

        try:
            await ctx.author.send(embed=embed)
        except:
            pass

        # Send to log channel if set
        if settings and settings['log_channel']:
            log_channel = ctx.guild.get_channel(settings['log_channel'])
            if log_channel:
                embed = create_embed(
                    title="🚨 Yeni Kullanıcı Raporu",
                    color=discord.Color.red()
                )
                embed.add_field(name="Raporlanan", value=member.mention, inline=True)
                embed.add_field(name="Raporlayan", value=ctx.author.mention, inline=True)
                embed.add_field(name="Kanal", value=ctx.channel.mention, inline=True)
                embed.add_field(name="Sebep", value=reason, inline=False)
                embed.timestamp = datetime.now()

                await log_channel.send(embed=embed)

        # Log the report
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "REPORT", reason
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reports(self, ctx, limit: int = 10):
        """Show recent reports."""
        lang = await self.bot.db.get_language(ctx.guild.id)

        if limit > 50:
            limit = 50

        reports = await self.bot.db.get_reports(ctx.guild.id, limit)

        if not reports:
            embed = create_embed(
                title="📋 Raporlar",
                description="Henüz hiç rapor bulunmuyor.",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)

        embed = create_embed(
            title=f"📋 Son {len(reports)} Rapor",
            color=discord.Color.orange()
        )

        for report in reports:
            reporter = ctx.guild.get_member(report['moderator_id'])
            reporter_name = reporter.display_name if reporter else "Bilinmiyor"

            target = ctx.guild.get_member(report['user_id'])
            target_name = target.display_name if target else f"ID: {report['user_id']}"

            timestamp = datetime.fromisoformat(report['timestamp']).strftime('%d/%m/%Y %H:%M')

            embed.add_field(
                name=f"Rapor - {timestamp}",
                value=f"**Raporlanan:** {target_name}\n**Raporlayan:** {reporter_name}\n**Sebep:** {report['reason']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def auditlog(self, ctx, hours: int = 24):
        """Show server audit log."""
        lang = await self.bot.db.get_language(ctx.guild.id)

        if hours > 168:  # Max 1 week
            hours = 168

        try:
            # Get audit log entries
            entries = []
            async for entry in ctx.guild.audit_logs(limit=50):
                if (datetime.now() - entry.created_at).total_seconds() < hours * 3600:
                    entries.append(entry)

            if not entries:
                embed = create_embed(
                    title="📋 Audit Log",
                    description=f"Son {hours} saatte herhangi bir aktivite bulunamadı.",
                    color=discord.Color.blue()
                )
                return await ctx.send(embed=embed)

            embed = create_embed(
                title=f"📋 Audit Log - Son {hours} saat",
                color=discord.Color.blue()
            )

            action_names = {
                discord.AuditLogAction.ban: "BAN",
                discord.AuditLogAction.unban: "UNBAN",
                discord.AuditLogAction.kick: "KICK",
                discord.AuditLogAction.member_update: "ÜYE GÜNCELLEME",
                discord.AuditLogAction.member_role_update: "ROL GÜNCELLEME",
                discord.AuditLogAction.channel_create: "KANAL OLUŞTURMA",
                discord.AuditLogAction.channel_delete: "KANAL SİLME",
                discord.AuditLogAction.channel_update: "KANAL GÜNCELLEME",
                discord.AuditLogAction.message_delete: "MESAJ SİLME",
                discord.AuditLogAction.message_bulk_delete: "TOPLU MESAJ SİLME"
            }

            for entry in entries[:15]:  # Limit to 15 entries
                action = action_names.get(entry.action, str(entry.action))
                user = entry.user.display_name if entry.user else "Bilinmiyor"
                target = entry.target

                if hasattr(target, 'display_name'):
                    target_name = target.display_name
                elif hasattr(target, 'name'):
                    target_name = target.name
                else:
                    target_name = str(target) if target else "Bilinmiyor"

                timestamp = entry.created_at.strftime('%d/%m/%Y %H:%M')
                reason = entry.reason or "Sebep yok"

                embed.add_field(
                    name=f"{action} - {timestamp}",
                    value=f"**Yapan:** {user}\n**Hedef:** {target_name}\n**Sebep:** {reason}",
                    inline=False
                )

            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = create_embed(
                title="❌ Hata",
                description="Audit log'u görüntülemek için yeterli iznim yok.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))