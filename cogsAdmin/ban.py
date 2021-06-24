import typing
from datetime import datetime

import discord

import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from crawler_utilities.handlers import logger
from utils.functions import get_next_case_num

log = logger.logger


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def tempban(self, ctx, member: typing.Optional[discord.Member], *, message):
        await self.TempBanCommand(ctx, member, message)

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def ban(self, ctx, member: typing.Optional[discord.Member], *, message):
        await self.BanCommand(ctx, member, message)

    # @cog_ext.cog_slash(name="tempban", description="Temporarily bans an user. (ban/unban)", guild_ids=GG.slashGuilds,
    #                    options=[
    #                        create_option(name="user", description="The user you want to ban.", option_type=6,
    #                                      required=True),
    #                        create_option(name="reason", description="The reason for temp-banning this person.",
    #                                      option_type=3, required=True)
    #                    ])
    # @GG.is_staff()
    # async def tempbanSlash(self, ctx, member: typing.Optional[discord.Member], *, message):
    #     await self.TempBanCommand(ctx, member, message)
    #
    # @cog_ext.cog_slash(name="ban", description="Bans an user permanently.", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="user", description="The user you want to ban.", option_type=6, required=True),
    #     create_option(name="reason", description="The reason for banning this person.", option_type=3, required=True)
    # ])
    # @GG.is_staff()
    # async def banSlash(self, ctx, member: typing.Optional[discord.Member], *, message):
    #     await self.BanCommand(ctx, member, message)

    async def TempBanCommand(self, ctx, member, message):
        if member is None:
            return await ctx.send(
                "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't temp-ban someone who isn't on the server.")

        memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member.id})
        caseId = await get_next_case_num()

        if memberDB is None:
            memberDB = {"server": ctx.guild.id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.TEMPBAN, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.author.id)
        await self.banPerson(case, ctx, member, memberDB, message)
        await member.unban(reason=message)

    async def BanCommand(self, ctx, member, message):
        if member is None:
            return await ctx.send(
                "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't ban someone who isn't on the server.")

        memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member.id})
        caseId = await get_next_case_num()

        if memberDB is None:
            memberDB = {"server": ctx.guild.id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.BAN, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.author.id)
        await self.banPerson(case, ctx, member, memberDB, message)

    async def banPerson(self, case, ctx, member, memberDB, message):
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
        await member.ban(reason=message)


def setup(bot):
    log.info("[Admin] Ban")
    bot.add_cog(Ban(bot))
