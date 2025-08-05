import discord
import asyncio
from discord.ext import commands
from utils.embeds import create_embed
from utils.helpers import get_text

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def createrole(self, ctx, name, color=None, *, permissions=None):
        """Create a new role."""
        # Parse color
        role_color = discord.Color.default()
        if color:
            try:
                if color.startswith('#'):
                    role_color = discord.Color(int(color[1:], 16))
                elif color.lower() in ['red', 'kırmızı']:
                    role_color = discord.Color.red()
                elif color.lower() in ['blue', 'mavi']:
                    role_color = discord.Color.blue()
                elif color.lower() in ['green', 'yeşil']:
                    role_color = discord.Color.green()
                elif color.lower() in ['yellow', 'sarı']:
                    role_color = discord.Color.yellow()
                elif color.lower() in ['purple', 'mor']:
                    role_color = discord.Color.purple()
                elif color.lower() in ['orange', 'turuncu']:
                    role_color = discord.Color.orange()
            except:
                pass
        
        # Create role
        role = await ctx.guild.create_role(
            name=name,
            color=role_color,
            reason=f"Role created by {ctx.author}"
        )
        
        embed = create_embed(
            title="✅ Rol oluşturuldu!",
            description=f"**Rol:** {role.mention}\n**Ad:** {name}\n**Renk:** {color or 'Varsayılan'}",
            color=role_color
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def deleterole(self, ctx, *, role):
        """Delete a role."""
        if role >= ctx.guild.me.top_role:
            embed = create_embed(
                title="❌ Bu rolü silemem!",
                description="Rol hiyerarşisinde benden yüksek veya eşit.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        role_name = role.name
        await role.delete(reason=f"Role deleted by {ctx.author}")
        
        embed = create_embed(
            title="🗑️ Rol silindi!",
            description=f"**{role_name}** rolü başarıyla silindi.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def roleinfo(self, ctx, *, role):
        """Show information about a role."""
        # Count members with this role
        member_count = len(role.members)
        
        # Get permissions
        perms = role.permissions
        enabled_perms = []
        if perms.administrator:
            enabled_perms.append("Yönetici")
        if perms.manage_guild:
            enabled_perms.append("Sunucuyu Yönet")
        if perms.manage_roles:
            enabled_perms.append("Rolleri Yönet")
        if perms.manage_channels:
            enabled_perms.append("Kanalları Yönet")
        if perms.manage_messages:
            enabled_perms.append("Mesajları Yönet")
        if perms.ban_members:
            enabled_perms.append("Üyeleri Yasakla")
        if perms.kick_members:
            enabled_perms.append("Üyeleri At")
        if perms.mention_everyone:
            enabled_perms.append("@everyone Etiketle")
        
        embed = create_embed(
            title=f"📋 {role.name} Rol Bilgisi",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue()
        )
        
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Üye Sayısı", value=member_count, inline=True)
        embed.add_field(name="Pozisyon", value=role.position, inline=True)
        embed.add_field(name="Renk", value=str(role.color), inline=True)
        embed.add_field(name="Ayrı Göster", value="Evet" if role.hoist else "Hayır", inline=True)
        embed.add_field(name="Etiketlenebilir", value="Evet" if role.mentionable else "Hayır", inline=True)
        
        if enabled_perms:
            embed.add_field(
                name="Önemli İzinler",
                value="\n".join(enabled_perms[:10]),  # Limit to 10 permissions
                inline=False
            )
        
        embed.add_field(name="Oluşturma Tarihi", value=role.created_at.strftime('%d/%m/%Y %H:%M'), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rolestats(self, ctx):
        """Show role distribution statistics."""
        roles = sorted(ctx.guild.roles[1:], key=lambda r: len(r.members), reverse=True)  # Exclude @everyone
        
        embed = create_embed(
            title=f"📊 {ctx.guild.name} Rol İstatistikleri",
            description=f"Toplam Rol: {len(roles)}",
            color=discord.Color.blue()
        )
        
        # Top 10 roles by member count
        top_roles = roles[:10]
        role_stats = ""
        for i, role in enumerate(top_roles):
            member_count = len(role.members)
            percentage = (member_count / ctx.guild.member_count) * 100
            role_stats += f"{i+1}. **{role.name}**: {member_count} üye ({percentage:.1f}%)\n"
        
        if role_stats:
            embed.add_field(name="En Çok Üyeli 10 Rol", value=role_stats, inline=False)
        
        # Empty roles
        empty_roles = [role for role in roles if len(role.members) == 0]
        if empty_roles:
            empty_role_names = [role.name for role in empty_roles[:10]]  # Show first 10
            embed.add_field(
                name=f"Boş Roller ({len(empty_roles)})",
                value="\n".join(empty_role_names) + ("..." if len(empty_roles) > 10 else ""),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def rolecolor(self, ctx, role, color):
        """Change role color."""
        if role >= ctx.guild.me.top_role:
            embed = create_embed(
                title="❌ Bu rolün rengini değiştiremem!",
                description="Rol hiyerarşisinde benden yüksek veya eşit.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Parse color
        try:
            if color.startswith('#'):
                new_color = discord.Color(int(color[1:], 16))
            elif color.lower() in ['red', 'kırmızı']:
                new_color = discord.Color.red()
            elif color.lower() in ['blue', 'mavi']:
                new_color = discord.Color.blue()
            elif color.lower() in ['green', 'yeşil']:
                new_color = discord.Color.green()
            elif color.lower() in ['yellow', 'sarı']:
                new_color = discord.Color.yellow()
            elif color.lower() in ['purple', 'mor']:
                new_color = discord.Color.purple()
            elif color.lower() in ['orange', 'turuncu']:
                new_color = discord.Color.orange()
            elif color.lower() in ['black', 'siyah']:
                new_color = discord.Color(0x000000)
            elif color.lower() in ['white', 'beyaz']:
                new_color = discord.Color(0xFFFFFF)
            else:
                raise ValueError("Geçersiz renk")
        except:
            embed = create_embed(
                title="❌ Geçersiz renk!",
                description="Desteklenen formatlar:\n• Hex kodu: `#FF0000`\n• Renk adları: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `black`, `white`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        old_color = role.color
        await role.edit(color=new_color, reason=f"Color changed by {ctx.author}")
        
        embed = create_embed(
            title="🎨 Rol rengi değiştirildi!",
            description=f"**Rol:** {role.mention}\n**Eski renk:** {old_color}\n**Yeni renk:** {new_color}",
            color=new_color
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def massrole(self, ctx, action, role, *, target="all"):
        """Mass add/remove roles from users."""
        if role >= ctx.guild.me.top_role:
            embed = create_embed(
                title="❌ Bu rolü yönetemem!",
                description="Rol hiyerarşisinde benden yüksek veya eşit.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if action.lower() not in ['add', 'remove', 'ekle', 'çıkar']:
            embed = create_embed(
                title="❌ Geçersiz eylem!",
                description="Geçerli eylemler: `add`, `remove`, `ekle`, `çıkar`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Determine target members
        if target.lower() in ['all', 'hepsi', 'tümü']:
            members = ctx.guild.members
        elif target.lower() in ['bots', 'botlar']:
            members = [m for m in ctx.guild.members if m.bot]
        elif target.lower() in ['humans', 'insanlar', 'kullanıcılar']:
            members = [m for m in ctx.guild.members if not m.bot]
        else:
            embed = create_embed(
                title="❌ Geçersiz hedef!",
                description="Geçerli hedefler: `all`, `bots`, `humans`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Confirm action
        member_count = len(members)
        embed = create_embed(
            title="⚠️ Toplu Rol İşlemi Onayı",
            description=f"**Eylem:** {action}\n**Rol:** {role.mention}\n**Hedef:** {target} ({member_count} üye)\n\n**Bu işlemi onaylıyor musunuz?**",
            color=discord.Color.orange()
        )
        
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = create_embed(
                    title="❌ İşlem iptal edildi!",
                    color=discord.Color.gray()
                )
                await confirm_msg.edit(embed=embed)
                return
            
        except asyncio.TimeoutError:
            embed = create_embed(
                title="⏰ Zaman aşımı!",
                description="İşlem otomatik olarak iptal edildi.",
                color=discord.Color.gray()
            )
            await confirm_msg.edit(embed=embed)
            return
        
        # Perform mass role operation
        success_count = 0
        failed_count = 0
        
        embed = create_embed(
            title="⏳ Toplu rol işlemi başlatıldı...",
            description=f"İşlem devam ediyor... 0/{member_count}",
            color=discord.Color.blue()
        )
        await confirm_msg.edit(embed=embed)
        
        for i, member in enumerate(members):
            try:
                if action.lower() in ['add', 'ekle']:
                    if role not in member.roles:
                        await member.add_roles(role, reason=f"Mass role add by {ctx.author}")
                        success_count += 1
                else:  # remove
                    if role in member.roles:
                        await member.remove_roles(role, reason=f"Mass role remove by {ctx.author}")
                        success_count += 1
                
                # Update progress every 10 members
                if (i + 1) % 10 == 0:
                    embed.description = f"İşlem devam ediyor... {i + 1}/{member_count}"
                    await confirm_msg.edit(embed=embed)
                    
            except:
                failed_count += 1
        
        # Final result
        embed = create_embed(
            title="✅ Toplu rol işlemi tamamlandı!",
            description=f"**Başarılı:** {success_count}\n**Başarısız:** {failed_count}\n**Toplam:** {success_count + failed_count}",
            color=discord.Color.green()
        )
        await confirm_msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))