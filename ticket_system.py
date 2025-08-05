import discord
from discord.ext import commands
import asyncio
from utils.embeds import create_embed
from utils.helpers import get_text

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setuptickets(self, ctx, category: discord.CategoryChannel = None):
        """Setup ticket system in a category."""
        if category is None:
            # Create ticket category
            category = await ctx.guild.create_category(
                name="🎫 Tickets",
                reason=f"Ticket category created by {ctx.author}"
            )
        
        # Save ticket category to database
        await self.bot.db.update_guild_setting(ctx.guild.id, 'ticket_category', category.id)
        
        # Create ticket creation channel
        ticket_channel = await ctx.guild.create_text_channel(
            name="ticket-oluştur",
            category=category,
            reason=f"Ticket creation channel by {ctx.author}"
        )
        
        # Setup permissions
        await ticket_channel.set_permissions(ctx.guild.default_role, 
                                           send_messages=False, read_messages=True)
        
        # Create ticket creation embed
        embed = create_embed(
            title="🎫 Destek Talep Sistemi",
            description="""
Destek talebinde bulunmak için aşağıdaki emojiye tıklayın.
Size özel bir destek kanalı oluşturulacak.

🎫 - Genel Destek
🐛 - Hata Bildirimi  
💡 - Öneri
❓ - Soru
            """.strip(),
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📋 Kurallar", value="""
• Sadece gerçek sorunlar için ticket açın
• Saygılı olun
• Sabırlı olun, size yardımcı olacağız
• Gereksiz ticket açmayın
        """.strip(), inline=False)
        
        message = await ticket_channel.send(embed=embed)
        
        # Add reactions
        reactions = ["🎫", "🐛", "💡", "❓"]
        for reaction in reactions:
            await message.add_reaction(reaction)
        
        # Save message ID for reaction handling
        await self.bot.db.execute_query(
            "INSERT OR REPLACE INTO ticket_messages VALUES (?, ?, ?)",
            (ctx.guild.id, message.id, ticket_channel.id)
        )
        
        success_embed = create_embed(
            title="✅ Ticket sistemi kuruldu!",
            description=f"**Kategori:** {category.mention}\n**Kanal:** {ticket_channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=success_embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle ticket creation reactions."""
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a ticket message
        result = await self.bot.db.execute_query(
            "SELECT * FROM ticket_messages WHERE message_id = ?",
            (payload.message_id,), fetch=True
        )
        
        if not result:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        user = guild.get_member(payload.user_id)
        if not user:
            return
        
        # Remove user's reaction
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, user)
        
        # Check if user already has an open ticket
        existing_ticket = discord.utils.find(
            lambda c: c.name == f"ticket-{user.name.lower()}" and isinstance(c, discord.TextChannel),
            guild.channels
        )
        
        if existing_ticket:
            try:
                await user.send(f"❌ Zaten açık bir ticket'ınız var: {existing_ticket.mention}")
            except:
                pass
            return
        
        # Get ticket category
        settings = await self.bot.db.get_guild_settings(guild.id)
        if not settings or not settings['ticket_category']:
            return
        
        category = guild.get_channel(settings['ticket_category'])
        if not category:
            return
        
        # Determine ticket type
        ticket_types = {
            "🎫": "genel",
            "🐛": "hata",
            "💡": "öneri", 
            "❓": "soru"
        }
        
        ticket_type = ticket_types.get(str(payload.emoji), "genel")
        
        # Create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Add staff roles if they exist
        staff_roles = []
        for role_name in ["Admin", "Moderator", "Staff", "Yetkili", "Mod"]:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                staff_roles.append(role)
        
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {user}"
        )
        
        # Create ticket embed
        embed = create_embed(
            title=f"🎫 Ticket - {ticket_type.title()}",
            description=f"**Kullanıcı:** {user.mention}\n**Tip:** {ticket_type.title()}\n**Oluşturulma:** {discord.utils.format_dt(discord.utils.utcnow())}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="📋 Yönergeler", value="""
• Sorununuzu detaylıca açıklayın
• Ekran görüntüleri ekleyebilirsiniz
• Yetkililerin yanıtını bekleyin
• Ticket'ı kapatmak için 🔒 emojisine tıklayın
        """.strip(), inline=False)
        
        if staff_roles:
            staff_mentions = " ".join([role.mention for role in staff_roles])
            embed.add_field(name="👥 Bildirim", value=f"Yetkili ekip: {staff_mentions}", inline=False)
        
        ticket_msg = await ticket_channel.send(f"{user.mention}", embed=embed)
        await ticket_msg.add_reaction("🔒")
        
        # Store ticket info
        self.active_tickets[ticket_channel.id] = {
            'user_id': user.id,
            'created_at': discord.utils.utcnow(),
            'type': ticket_type
        }
        
        # Send confirmation DM
        try:
            dm_embed = create_embed(
                title="✅ Ticket oluşturuldu!",
                description=f"Ticket kanalınız: {ticket_channel.mention}",
                color=discord.Color.green()
            )
            await user.send(embed=dm_embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle ticket close reactions."""
        if payload.user_id == self.bot.user.id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        channel = guild.get_channel(payload.channel_id)
        if not channel or not channel.name.startswith("ticket-"):
            return
        
        if str(payload.emoji) == "🔒":
            user = guild.get_member(payload.user_id)
            if not user:
                return
            
            # Check if user has permission to close ticket
            ticket_info = self.active_tickets.get(channel.id)
            if not ticket_info:
                return
            
            is_ticket_owner = user.id == ticket_info['user_id']
            is_staff = any(role.name in ["Admin", "Moderator", "Staff", "Yetkili", "Mod"] 
                          for role in user.roles)
            
            if not (is_ticket_owner or is_staff or user.guild_permissions.administrator):
                return
            
            # Confirmation
            embed = create_embed(
                title="⚠️ Ticket Kapatma Onayı",
                description="Bu ticket'ı kapatmak istediğinizden emin misiniz?\n\n✅ - Kapat\n❌ - İptal",
                color=discord.Color.orange()
            )
            
            confirm_msg = await channel.send(embed=embed)
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")
            
            def check(reaction, reaction_user):
                return (reaction_user == user and 
                       str(reaction.emoji) in ["✅", "❌"] and 
                       reaction.message.id == confirm_msg.id)
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "✅":
                    await self.close_ticket(channel, user, ticket_info)
                else:
                    await confirm_msg.delete()
                    
            except asyncio.TimeoutError:
                await confirm_msg.delete()
    
    async def close_ticket(self, channel, closer, ticket_info):
        """Close a ticket channel."""
        # Create transcript
        messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            if not message.author.bot or message.embeds:
                messages.append(f"[{message.created_at.strftime('%d/%m/%Y %H:%M')}] {message.author}: {message.content}")
        
        transcript = "\n".join(messages)
        
        # Send transcript to user
        ticket_owner = channel.guild.get_member(ticket_info['user_id'])
        if ticket_owner:
            try:
                transcript_embed = create_embed(
                    title="🎫 Ticket Kapatıldı",
                    description=f"Ticket'ınız {closer.mention} tarafından kapatıldı.",
                    color=discord.Color.red()
                )
                
                # Create transcript file
                transcript_file = discord.File(
                    fp=transcript.encode('utf-8'),
                    filename=f"ticket-{ticket_owner.name}-{channel.created_at.strftime('%Y%m%d')}.txt"
                )
                
                await ticket_owner.send(embed=transcript_embed, file=transcript_file)
            except:
                pass
        
        # Log ticket closure
        settings = await self.bot.db.get_guild_settings(channel.guild.id)
        if settings and settings['log_channel']:
            log_channel = channel.guild.get_channel(settings['log_channel'])
            if log_channel:
                log_embed = create_embed(
                    title="🎫 Ticket Kapatıldı",
                    description=f"""
**Ticket:** {channel.name}
**Sahip:** {ticket_owner.mention if ticket_owner else "Bilinmiyor"}
**Kapatan:** {closer.mention}
**Süre:** {discord.utils.format_dt(ticket_info['created_at'], 'R')}
                    """.strip(),
                    color=discord.Color.red()
                )
                await log_channel.send(embed=log_embed)
        
        # Remove from active tickets
        if channel.id in self.active_tickets:
            del self.active_tickets[channel.id]
        
        # Delete channel after 5 seconds
        await channel.send("🎫 Ticket 5 saniye içinde kapatılacak...")
        await asyncio.sleep(5)
        await channel.delete(reason=f"Ticket closed by {closer}")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketstats(self, ctx):
        """Show ticket system statistics."""
        # Get ticket channels
        ticket_channels = [c for c in ctx.guild.channels 
                          if isinstance(c, discord.TextChannel) and c.name.startswith("ticket-")]
        
        embed = create_embed(
            title="🎫 Ticket İstatistikleri",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📊 Genel", value=f"""
**Aktif Ticket:** {len(ticket_channels)}
**Bugün Açılan:** {len(self.active_tickets)}
**Toplam Kanal:** {len([c for c in ctx.guild.channels if c.name.startswith("ticket")])}
        """.strip(), inline=False)
        
        if ticket_channels:
            ticket_list = "\n".join([f"• {channel.mention}" for channel in ticket_channels[:10]])
            if len(ticket_channels) > 10:
                ticket_list += f"\n... ve {len(ticket_channels) - 10} tane daha"
            
            embed.add_field(name="📋 Aktif Ticketlar", value=ticket_list, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))