import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from utils.helpers import get_text, parse_time
from utils.permissions import has_permissions, hierarchy_check
from utils.embeds import create_embed

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ban(self, ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
        """Ban a user from the server."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Hierarchy check
        if not hierarchy_check(ctx.author, member, ctx.guild.owner):
            embed = create_embed(
                title="❌ " + get_text(self.bot.languages, lang, 'errors.hierarchy_error'),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Send DM before ban
        try:
            dm_text = get_text(self.bot.languages, lang, 'commands.ban.dm_message')
            await member.send(dm_text.format(guild=ctx.guild.name, reason=reason))
        except:
            pass
        
        # Ban the member
        await member.ban(reason=f"{ctx.author}: {reason}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "BAN", reason
        )
        
        # Send success message
        success_text = get_text(self.bot.languages, lang, 'commands.ban.success')
        reason_text = get_text(self.bot.languages, lang, 'commands.ban.reason')
        
        embed = create_embed(
            title=success_text.format(user=str(member)),
            description=reason_text.format(reason=reason),
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unban(self, ctx, user_id: int, *, reason="Sebep belirtilmedi"):
        """Unban a user from the server."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            
            # Remove from temp bans if exists
            await self.bot.db.remove_temp_ban(ctx.guild.id, user_id)
            
            # Log the action
            await self.bot.db.add_mod_log(
                ctx.guild.id, ctx.author.id, user_id, "UNBAN", reason
            )
            
            success_text = get_text(self.bot.languages, lang, 'commands.unban.success')
            embed = create_embed(
                title=success_text.format(user=str(user)),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            not_banned_text = get_text(self.bot.languages, lang, 'commands.unban.not_banned')
            embed = create_embed(
                title=not_banned_text,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kick(self, ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
        """Kick a user from the server."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Hierarchy check
        if not hierarchy_check(ctx.author, member, ctx.guild.owner):
            embed = create_embed(
                title="❌ " + get_text(self.bot.languages, lang, 'errors.hierarchy_error'),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Send DM before kick
        try:
            dm_text = get_text(self.bot.languages, lang, 'commands.kick.dm_message')
            await member.send(dm_text.format(guild=ctx.guild.name, reason=reason))
        except:
            pass
        
        # Kick the member
        await member.kick(reason=f"{ctx.author}: {reason}")
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "KICK", reason
        )
        
        # Send success message
        success_text = get_text(self.bot.languages, lang, 'commands.kick.success')
        reason_text = get_text(self.bot.languages, lang, 'commands.kick.reason')
        
        embed = create_embed(
            title=success_text.format(user=str(member)),
            description=reason_text.format(reason=reason),
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mute(self, ctx, member: discord.Member, duration=None, *, reason="Sebep belirtilmedi"):
        """Mute a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        
        if not settings or not settings['mute_role']:
            no_role_text = get_text(self.bot.languages, lang, 'commands.mute.no_mute_role')
            prefix = await self.bot.get_prefix(ctx.message)
            embed = create_embed(
                title=no_role_text.format(prefix=prefix),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        mute_role = ctx.guild.get_role(settings['mute_role'])
        if not mute_role:
            no_role_text = get_text(self.bot.languages, lang, 'commands.mute.no_mute_role')
            prefix = await self.bot.get_prefix(ctx.message)
            embed = create_embed(
                title=no_role_text.format(prefix=prefix),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Check if already muted
        if mute_role in member.roles:
            already_muted_text = get_text(self.bot.languages, lang, 'commands.mute.already_muted')
            embed = create_embed(
                title=already_muted_text,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Add mute role
        await member.add_roles(mute_role, reason=f"{ctx.author}: {reason}")
        
        # Handle duration
        expires_at = None
        if duration:
            duration_seconds = parse_time(duration)
            if duration_seconds:
                expires_at = datetime.now() + timedelta(seconds=duration_seconds)
                await self.bot.db.add_mute(ctx.guild.id, member.id, expires_at, reason)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "MUTE", reason
        )
        
        # Send success message
        if expires_at:
            success_text = get_text(self.bot.languages, lang, 'commands.mute.success')
            embed = create_embed(
                title=success_text.format(user=str(member), duration=duration),
                description=f"Sebep: {reason}",
                color=discord.Color.orange()
            )
        else:
            permanent_text = get_text(self.bot.languages, lang, 'commands.mute.permanent')
            embed = create_embed(
                title=permanent_text.format(user=str(member)),
                description=f"Sebep: {reason}",
                color=discord.Color.orange()
            )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        
        if not settings or not settings['mute_role']:
            return
        
        mute_role = ctx.guild.get_role(settings['mute_role'])
        if not mute_role or mute_role not in member.roles:
            not_muted_text = get_text(self.bot.languages, lang, 'commands.unmute.not_muted')
            embed = create_embed(
                title=not_muted_text,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Remove mute role
        await member.remove_roles(mute_role, reason=f"Unmuted by {ctx.author}")
        
        # Remove from database
        await self.bot.db.remove_mute(ctx.guild.id, member.id)
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "UNMUTE", "Manual unmute"
        )
        
        success_text = get_text(self.bot.languages, lang, 'commands.unmute.success')
        embed = create_embed(
            title=success_text.format(user=str(member)),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def warn(self, ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
        """Warn a user."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        # Add warning to database
        await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        
        # Send DM to user
        try:
            dm_text = get_text(self.bot.languages, lang, 'commands.warn.dm_message')
            await member.send(dm_text.format(guild=ctx.guild.name, reason=reason))
        except:
            pass
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, member.id, "WARN", reason
        )
        
        success_text = get_text(self.bot.languages, lang, 'commands.warn.success')
        embed = create_embed(
            title=success_text.format(user=str(member), reason=reason),
            color=discord.Color.yellow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """Show user warnings."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        warnings = await self.bot.db.get_warnings(ctx.guild.id, member.id)
        
        title_text = get_text(self.bot.languages, lang, 'commands.warnings.title')
        
        if not warnings:
            no_warnings_text = get_text(self.bot.languages, lang, 'commands.warnings.no_warnings')
            embed = create_embed(
                title=title_text.format(user=str(member)),
                description=no_warnings_text,
                color=discord.Color.green()
            )
        else:
            warning_format = get_text(self.bot.languages, lang, 'commands.warnings.warning_format')
            description = ""
            
            for warning in warnings[:10]:  # Show max 10 warnings
                date = warning[5][:10] if len(warning) > 5 else "N/A"
                description += warning_format.format(
                    id=warning[0],
                    reason=warning[4],
                    date=date,
                    moderator=warning[3]
                ) + "\n\n"
            
            embed = create_embed(
                title=title_text.format(user=str(member)),
                description=description,
                color=discord.Color.orange()
            )
            embed.add_field(name="Toplam Uyarı", value=str(len(warnings)), inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """Clear user warnings."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        await self.bot.db.clear_warnings(ctx.guild.id, member.id)
        
        success_text = get_text(self.bot.languages, lang, 'commands.clearwarns.success')
        embed = create_embed(
            title=success_text.format(user=str(member)),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['clear'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def purge(self, ctx, amount: int):
        """Delete messages."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if amount < 1 or amount > 100:
            invalid_text = get_text(self.bot.languages, lang, 'commands.purge.invalid_amount')
            embed = create_embed(
                title=invalid_text,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Delete messages
        deleted = await ctx.channel.purge(limit=amount)
        
        success_text = get_text(self.bot.languages, lang, 'commands.purge.success')
        embed = create_embed(
            title=success_text.format(count=len(deleted)),
            color=discord.Color.green()
        )
        
        # Send and delete after 5 seconds
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
        
        # Log the action
        await self.bot.db.add_mod_log(
            ctx.guild.id, ctx.author.id, 0, "PURGE", f"{len(deleted)} messages"
        )
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx, channel=None):
        """Lock a channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        if channel is None:
            channel = ctx.channel
        
        # Check if already locked
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            already_locked_text = get_text(self.bot.languages, lang, 'commands.lock.already_locked')
            embed = create_embed(
                title=already_locked_text,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Lock the channel
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        success_text = get_text(self.bot.languages, lang, 'commands.lock.success')
        embed = create_embed(
            title=success_text,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel=None):
        """Unlock a channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        if channel is None:
            channel = ctx.channel
        
        # Check if locked
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is not False:
            not_locked_text = get_text(self.bot.languages, lang, 'commands.unlock.not_locked')
            embed = create_embed(
                title=not_locked_text,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Unlock the channel
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        success_text = get_text(self.bot.languages, lang, 'commands.unlock.success')
        embed = create_embed(
            title=success_text,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Set slowmode for a channel."""
        lang = await self.bot.db.get_language(ctx.guild.id)
        
        if seconds < 0 or seconds > 21600:
            invalid_text = get_text(self.bot.languages, lang, 'commands.slowmode.invalid_time')
            embed = create_embed(
                title=invalid_text,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await ctx.channel.edit(slowmode_delay=seconds)
        
        if seconds == 0:
            disabled_text = get_text(self.bot.languages, lang, 'commands.slowmode.disabled')
            embed = create_embed(
                title=disabled_text,
                color=discord.Color.green()
            )
        else:
            success_text = get_text(self.bot.languages, lang, 'commands.slowmode.success')
            embed = create_embed(
                title=success_text.format(seconds=seconds),
                color=discord.Color.green()
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
