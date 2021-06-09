import typing

import discord

import utils.globals as GG

from discord.ext import commands
from utils import logger

log = logger.logger


def getGuild(self, payload):
    guild = self.bot.get_guild(payload.guild_id)
    return guild


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, hidden=True)
    @commands.guild_only()
    @GG.is_staff()
    async def role(self, ctx):
        if GG.is_staff_bool:
            return await ctx.send("This is the command that allows you to add roles that people can add themselves by command.")
        else:
            return await ctx.send("This is the command that allows you to change your cosmetic role.\nUse ``role list`` to check which ones you have unlocked.\nOr use ``role change <id>`` to change your role.")

    @role.command(name='add')
    @commands.guild_only()
    @GG.is_staff()
    async def role_add(self, ctx, member: typing.Optional[discord.Member] = None, role: typing.Optional[discord.Role] = None):
        if member is None or role is None:
            return await ctx.send("Either the member id is wrong, or the role id is not a role id, please check both.")

        await GG.MDB['userroles'].insert_one({"guildId": ctx.guild.id, "userId": member.id, "roleId": role.id})

    @role.command(name='list')
    @commands.guild_only()
    async def role_list(self, ctx, member: typing.Optional[discord.Member] = None, role: typing.Optional[discord.Role] = None):
        pass

    @role.command(name='change')
    @commands.guild_only()
    async def role_change(self, ctx, role: typing.Optional[discord.Role] = None):
        pass





def setup(bot):
    log.info("[Cog] Roles")
    bot.add_cog(Roles(bot))
