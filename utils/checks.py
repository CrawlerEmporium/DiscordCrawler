import discord
from discord.ext import commands

import utils.globals as GG


def is_staff_trouble():
    async def predicate(ctx):
        global allowed
        if isinstance(ctx.author, discord.Member):
            if ctx.author.roles is not None:
                for r in ctx.author.roles:
                    if r.id in GG.STAFF or r.id == 593720945324326914:
                        allowed = True
                        break
                    else:
                        allowed = False

                if ctx.author.id == GG.OWNER or ctx.author.id == ctx.guild.owner_id:
                    allowed = True
            else:
                allowed = False
        else:
            try:
                if ctx.author.id == GG.OWNER or ctx.author.id == ctx.guild.owner_id:
                    allowed = True
                else:
                    allowed = False
            except Exception:
                allowed = False

        try:
            if ctx.guild.get_member(ctx.author.id).guild_permissions.administrator:
                allowed = True
        except:
            pass

        return allowed

    return commands.check(predicate)
