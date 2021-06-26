from datetime import datetime

import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from crawler_utilities.handlers import logger

from crawler_utilities.utils.functions import get_next_num

log = logger.logger

class Note(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def note(self, ctx, member, *, message):
        await self.noteCommand(ctx, member, message)

    # @cog_ext.cog_slash(name="note", description="Adds a note to an user", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="userId", description="The user Id of the user you want to add the note to.", option_type=3, required=True),
    #     create_option(name="message", description="The message the nout should contain", option_type=3, required=True)
    # ])
    # @GG.is_staff()
    # async def noteSlash(self, ctx, member, *, message):
    #     await self.noteCommand(ctx, member, message)

    async def noteCommand(self, ctx, member, message):
        member = int(member)
        if ctx.guild.get_member(member) is None:
            await ctx.send(
                "Member wasn't found on the server. Inserting note as a general snowflake.\n\nPlease check if this is actually a member, it might be a channel/message id.")
        memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member})
        caseId = await get_next_num(self.bot.mdb['properties'], 'caseId')
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
