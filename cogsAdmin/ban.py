import typing
from datetime import datetime

import discord
from discord import Option, slash_command

import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs
from crawler_utilities.handlers import logger

from crawler_utilities.utils.functions import get_next_num

log = logger.logger


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "ban"

    @slash_command(**get_command_kwargs(cogName, 'ban'))
    async def ban(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, 'ban.member')), message: Option(str, **get_parameter_kwargs(cogName, 'ban.message'))):

        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.BanCommand(ctx, member, message)

    async def BanCommand(self, ctx, member, message):
        if member is None:
            return await ctx.send(
                "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't ban someone who isn't on the server.")

        memberDB = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member.id})
        caseId = await get_next_num(self.bot.mdb['properties'], 'caseId')

        if memberDB is None:
            memberDB = {"server": ctx.interaction.guild_id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.BAN, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.interaction.user.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.interaction.guild_id, "user": member.id}, {"$set": memberDB}, upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.respond(embed=embed)

        decisionChannelExist = await GG.MDB['channelinfo'].find_one({"guild": ctx.interaction.guild_id, "type": "MODDECISION"})
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
            await ctx.send(f"DM with info send to {member}")
        except discord.Forbidden:
            await ctx.send(f"Message failed to send. (Not allowed to DM)")

        await member.ban(reason=message)


def setup(bot):
    log.info("[Admin] Ban")
    bot.add_cog(Ban(bot))
