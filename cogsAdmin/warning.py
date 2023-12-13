from datetime import datetime

import discord
from discord import slash_command, Option

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import globals as GG

from crawler_utilities.utils.functions import get_next_num
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs

log = GG.log


class Warning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "warn"

    @slash_command(**get_command_kwargs(cogName, "warn"))
    @commands.guild_only()
    async def warn(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, "warn.member")), message: Option(str, **get_parameter_kwargs(cogName, "warn.message"))):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        await self.warnCommand(ctx, member, message)

    async def warnCommand(self, ctx, member, message):
        memberDB = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member.id})
        caseId = await get_next_num(self.bot.mdb['properties'], 'caseId')

        if memberDB is None:
            memberDB = {"server": ctx.interaction.guild_id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.WARNING, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.interaction.user.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.interaction.guild_id, "user": member.id}, {"$set": memberDB}, upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.send(embed=embed)

        decisionChannelExist = await GG.MDB['channelinfo'].find_one(
            {"guild": ctx.interaction.guild_id, "type": "MODDECISION"})
        if decisionChannelExist is not None:
            modDecisionChannel = await self.bot.fetch_channel(decisionChannelExist['channel'])
            embed = await getModDecisionEmbed(ctx, case)
            await modDecisionChannel.send(embed=embed)

        if member.dm_channel is not None:
            DM = member.dm_channel
        else:
            DM = await member.create_dm()

        try:
            embed = await getCaseTargetEmbed(ctx, case)
            await DM.send(embed=embed)
            await ctx.respond(f"DM with info send to {member}")
        except discord.Forbidden:
            await ctx.respond(f"Message failed to send. (Not allowed to DM)")


def setup(bot):
    log.info("[Admin] Warning")
    bot.add_cog(Warning(bot))
