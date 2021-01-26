import typing
from datetime import datetime

import discord
import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import logger
from utils.functions import get_next_case_num

log = logger.logger


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def tempban(self, ctx, member: typing.Optional[discord.Member], *, message):
        if member is None:
            return await ctx.send("Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't temp-ban someone who isn't on the server.")

        memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member.id})
        caseId = await get_next_case_num()

        if memberDB is None:
            memberDB = {"server": ctx.guild.id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.TEMPBAN, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.author.id)
        await self.banPerson(case, ctx, member, memberDB, message)
        await member.unban(reason=message)

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def ban(self, ctx, member: typing.Optional[discord.Member], *, message):
        if member is None:
            return await ctx.send("Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't ban someone who isn't on the server.")

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
