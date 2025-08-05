import discord
from discord.ext import commands

def has_permissions(**perms):
    """Check if user has required permissions."""
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        
        permissions = ctx.author.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        
        if missing:
            raise commands.MissingPermissions(missing)
        
        return True
    
    return commands.check(predicate)

def hierarchy_check(moderator, target, owner):
    """Check if moderator can perform action on target."""
    # Owner can do anything
    if moderator == owner:
        return True
    
    # Cannot target owner
    if target == owner:
        return False
    
    # Cannot target self
    if moderator == target:
        return False
    
    # Check role hierarchy
    if moderator.top_role <= target.top_role:
        return False
    
    return True

def can_bot_moderate(bot_member, target):
    """Check if bot can moderate target."""
    # Bot needs higher role than target
    if bot_member.top_role <= target.top_role:
        return False
    
    # Bot cannot moderate owner
    if target == target.guild.owner:
        return False
    
    return True

async def check_hierarchy(ctx, target):
    """Check moderation hierarchy."""
    # Check if user can moderate target
    if not hierarchy_check(ctx.author, target, ctx.guild.owner):
        raise commands.CheckFailure("You cannot perform this action on this user due to role hierarchy.")
    
    # Check if bot can moderate target  
    if not can_bot_moderate(ctx.guild.me, target):
        raise commands.CheckFailure("I cannot perform this action on this user due to role hierarchy.")
    
    return True

def is_moderator():
    """Check if user is a moderator."""
    async def predicate(ctx):
        # Administrator
        if ctx.author.guild_permissions.administrator:
            return True
        
        # Has any moderation permissions
        perms = ctx.author.guild_permissions
        mod_perms = [
            perms.ban_members,
            perms.kick_members, 
            perms.manage_messages,
            perms.manage_roles,
            perms.manage_channels
        ]
        
        if any(mod_perms):
            return True
        
        raise commands.CheckFailure("You need moderation permissions to use this command.")
    
    return commands.check(predicate)

def is_admin():
    """Check if user is administrator."""
    async def predicate(ctx):
        if not ctx.author.guild_permissions.administrator:
            raise commands.CheckFailure("You need administrator permissions to use this command.")
        return True
    
    return commands.check(predicate)

def bot_has_permissions(**perms):
    """Check if bot has required permissions."""
    async def predicate(ctx):
        permissions = ctx.guild.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        
        if missing:
            raise commands.BotMissingPermissions(missing)
        
        return True
    
    return commands.check(predicate)
