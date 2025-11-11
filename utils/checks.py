import discord
from discord.ext import commands

import utils.globals as GG

def _check_permissions(ctx, perms):
    ch = ctx.channel
    author = ctx.author
    try:
        resolved = ch.permissions_for(author)
    except AttributeError:
        resolved = None
    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def _role_or_permissions(ctx, role_filter, **perms):
    if _check_permissions(ctx, perms):
        return True

    ch = ctx.message.channel
    author = ctx.message.author
    if isinstance(ch, discord.abc.PrivateChannel):
        return False  # can't have roles in PMs

    try:
        role = discord.utils.find(role_filter, author.roles)
    except:
        return False
    return role is not None


def admin_or_permissions(**perms):
    def predicate(ctx):
        admin_role = "Bot Admin"
        if _role_or_permissions(ctx, lambda r: r.name.lower() == admin_role.lower(), **perms):
            return True
        raise commands.CheckFailure(
            f"You require a role named Bot Admin or these permissions to run this command: {', '.join(perms)}")

    return commands.check(predicate)

def is_staff_trouble():
    async def predicate(ctx):
        allowed = False
        author = ctx.author

        if isinstance(author, discord.Member):
            if any(r.id in GG.STAFF or r.id == 593720945324326914 for r in author.roles):
                allowed = True
            elif author.id in {GG.OWNER, ctx.guild.owner_id}:
                allowed = True
            elif ctx.guild.get_member(author.id) is not None and ctx.guild.get_member(author.id).guild_permissions.administrator:
                allowed = True

        return allowed

    return commands.check(predicate)

def is_trouble(ctx):
    allowed = False
    author = ctx.author

    if isinstance(author, discord.Member):
        if any(r.id in GG.STAFF or r.id == 593720945324326914 for r in author.roles):
            allowed = True
        elif author.id in {GG.OWNER, ctx.guild.owner_id}:
            allowed = True
        elif ctx.guild.get_member(author.id) is not None and ctx.guild.get_member(author.id).guild_permissions.administrator:
            allowed = True

    return allowed
