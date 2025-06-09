from datetime import datetime

import discord
from discord import Option, slash_command

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from cogsAdmin.utils import banHandler
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs
from utils import globals as GG

from crawler_utilities.utils.functions import get_next_num

log = GG.log


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "ban"

    @slash_command(**get_command_kwargs(cogName, 'ban'))
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def ban(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, 'ban.member')),
                  message: Option(str, **get_parameter_kwargs(cogName, 'ban.message'))):
        await ctx.defer()
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        return await banHandler.BanCommand(self, ctx, member, message, False)


def setup(bot):
    log.info("[Admin] Ban")
    bot.add_cog(Ban(bot))
