import typing
from datetime import datetime

import discord

import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import logger
from utils.functions import get_next_case_num

log = logger.logger


class Warning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def warn(self, ctx, member: typing.Optional[discord.Member], *, message):
        await self.warnCommand(ctx, member, message)

    # @cog_ext.cog_slash(name="warn", description="Warns an user.", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="user", description="The user you want to warn.", option_type=6, required=True),
    #     create_option(name="reason", description="The reason for warning this person.", option_type=3, required=True)
    # ])
    # @GG.is_staff()
    # async def warnSlash(self, ctx, member: typing.Optional[discord.Member], *, message):
    #     await self.warnCommand(ctx, member, message)

    async def warnCommand(self, ctx, member, message):
        if member is None:
            return await ctx.send(
                "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't warn someone who isn't on the server.")

        memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member.id})
        caseId = await get_next_case_num()

        if memberDB is None:
            memberDB = {"server": ctx.guild.id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.WARNING, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.author.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.guild.id, "user": member.id}, {"$set": memberDB}, upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.send(embed=embed)

        decisionChannelExist = await GG.MDB['channelinfo'].find_one(
            {"guild": ctx.message.guild.id, "type": "MODDECISION"})
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


    @commands.command()
    @commands.is_owner()
    async def webhook(self, ctx):
        await ctx.channel.create_webhook(name="Fake Player Quoting")

        webhooks = await ctx.channel.webhooks()
        before = len(webhooks)
        for x in webhooks:
            if(x.user == self.bot.user):
                await x.delete()

        webhooks = await ctx.channel.webhooks()
        after = len(webhooks)

        print(before, after)


def setup(bot):
    log.info("[Admin] Warning")
    bot.add_cog(Warning(bot))
