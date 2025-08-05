import discord
from discord.ext import commands
from utils.embeds import create_embed

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {}
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def reactionrole(self, ctx, message_id: int, emoji, *, role: discord.Role):
        """Add a reaction role to a message."""
        if role >= ctx.guild.me.top_role:
            embed = create_embed(
                title="❌ Rol çok yüksek!",
                description="Bu rolü veremem çünkü benim rolümden daha yüksek.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        try:
            # Get the message
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            embed = create_embed(
                title="❌ Mesaj bulunamadı!",
                description="Belirtilen ID'ye sahip mesaj bu kanalda bulunamadı.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Add reaction to message
        await message.add_reaction(emoji)
        
        # Store in database
        await self.bot.db.execute_query(
            "INSERT OR REPLACE INTO reaction_roles VALUES (?, ?, ?, ?, ?)",
            (ctx.guild.id, message.id, emoji, role.id, ctx.channel.id)
        )
        
        # Store in memory
        key = f"{message.id}_{emoji}"
        self.reaction_roles[key] = {
            'guild_id': ctx.guild.id,
            'role_id': role.id,
            'channel_id': ctx.channel.id
        }
        
        embed = create_embed(
            title="✅ Reaction role eklendi!",
            description=f"**Mesaj:** [Mesaja git]({message.jump_url})\n**Emoji:** {emoji}\n**Rol:** {role.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removereactionrole(self, ctx, message_id: int, emoji):
        """Remove a reaction role from a message."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.remove_reaction(emoji, ctx.guild.me)
        except:
            pass
        
        # Remove from database
        await self.bot.db.execute_query(
            "DELETE FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (ctx.guild.id, message_id, emoji)
        )
        
        # Remove from memory
        key = f"{message_id}_{emoji}"
        if key in self.reaction_roles:
            del self.reaction_roles[key]
        
        embed = create_embed(
            title="✅ Reaction role kaldırıldı!",
            description=f"**Mesaj ID:** {message_id}\n**Emoji:** {emoji}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def reactionrolepanel(self, ctx, *, title="Rol Seçimi"):
        """Create a reaction role panel."""
        embed = create_embed(
            title=f"🎭 {title}",
            description="Aşağıdaki emojilere tıklayarak rollerinizi seçin:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📋 Nasıl Kullanılır?", value="""
• Emoji'ye tıklayarak rol alın
• Tekrar tıklayarak rolü bırakın
• Birden fazla rol alabilirsiniz
        """.strip(), inline=False)
        
        panel_message = await ctx.send(embed=embed)
        
        embed = create_embed(
            title="✅ Reaction role paneli oluşturuldu!",
            description=f"Panel mesaj ID'si: `{panel_message.id}`\nŞimdi `!reactionrole {panel_message.id} <emoji> <rol>` komutuyla roller ekleyin.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def reactionrolelist(self, ctx):
        """List all reaction roles in the server."""
        # Get reaction roles from database
        result = await self.bot.db.execute_query(
            "SELECT * FROM reaction_roles WHERE guild_id = ?",
            (ctx.guild.id,), fetch=True
        )
        
        if not result:
            embed = create_embed(
                title="📋 Reaction Role Listesi",
                description="Bu sunucuda hiç reaction role ayarlanmamış.",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        embed = create_embed(
            title="📋 Reaction Role Listesi",
            color=discord.Color.blue()
        )
        
        for i, (guild_id, message_id, emoji, role_id, channel_id) in enumerate(result[:20]):  # Limit 20
            role = ctx.guild.get_role(role_id)
            channel = ctx.guild.get_channel(channel_id)
            
            if role and channel:
                embed.add_field(
                    name=f"{i+1}. {emoji} → {role.name}",
                    value=f"[Mesaj]({f'https://discord.com/channels/{guild_id}/{channel_id}/{message_id}'}) • {channel.mention}",
                    inline=False
                )
        
        if len(result) > 20:
            embed.set_footer(text=f"... ve {len(result) - 20} tane daha")
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Load reaction roles from database on bot start."""
        try:
            result = await self.bot.db.execute_query(
                "SELECT * FROM reaction_roles", fetch=True
            )
            
            for guild_id, message_id, emoji, role_id, channel_id in result:
                key = f"{message_id}_{emoji}"
                self.reaction_roles[key] = {
                    'guild_id': guild_id,
                    'role_id': role_id,
                    'channel_id': channel_id
                }
            
            print(f"✅ {len(result)} reaction role yüklendi!")
            
        except Exception as e:
            print(f"❌ Reaction roles yüklenirken hata: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction role assignment."""
        if payload.user_id == self.bot.user.id:
            return
        
        key = f"{payload.message_id}_{payload.emoji}"
        if key not in self.reaction_roles:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        role_id = self.reaction_roles[key]['role_id']
        role = guild.get_role(role_id)
        
        if not role:
            return
        
        if role not in member.roles:
            try:
                await member.add_roles(role, reason="Reaction role")
                
                # Send DM notification
                try:
                    embed = create_embed(
                        title="✅ Rol verildi!",
                        description=f"**{guild.name}** sunucusunda **{role.name}** rolü aldınız.",
                        color=discord.Color.green()
                    )
                    await member.send(embed=embed)
                except:
                    pass
                    
            except discord.HTTPException:
                pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction role removal."""
        if payload.user_id == self.bot.user.id:
            return
        
        key = f"{payload.message_id}_{payload.emoji}"
        if key not in self.reaction_roles:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        role_id = self.reaction_roles[key]['role_id']
        role = guild.get_role(role_id)
        
        if not role:
            return
        
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
                
                # Send DM notification
                try:
                    embed = create_embed(
                        title="❌ Rol alındı!",
                        description=f"**{guild.name}** sunucusunda **{role.name}** rolünüz alındı.",
                        color=discord.Color.red()
                    )
                    await member.send(embed=embed)
                except:
                    pass
                    
            except discord.HTTPException:
                pass

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))