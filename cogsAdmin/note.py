import typing
from datetime import datetime

import discord
import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import logger
from utils.functions import get_next_case_num

log = logger.logger

class Note(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def note(self, ctx, member: int, *, message):
        if ctx.guild.get_member(member) is None:
            await ctx.send("Member wasn't found on the server. Inserting note as a general snowflake.\n\nPlease check if this is actually a member, it might be a channel/message id.")

        memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member})
        caseId = await get_next_case_num()

        if memberDB is None:
            memberDB = {"server": ctx.guild.id, "user": member, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)

        case = Case(caseId, CaseType.NOTE, CaseStatus.OPEN, message, datetime.now(), member, ctx.author.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.guild.id, "user": member}, {"$set": memberDB}, upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.send(embed=embed)

def setup(bot):
    log.info("[Admin] Note")
    bot.add_cog(Note(bot))
