from datetime import datetime

import discord
from discord import slash_command, Option

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import globals as GG

from crawler_utilities.utils.functions import get_next_num
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs

log = GG.log


class Note(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "note"

    @slash_command(**get_command_kwargs(cogName,"note"))
    @commands.guild_only()
    async def note(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, "note.member")), message: Option(str, **get_parameter_kwargs(cogName, "note.message"))):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.noteCommand(ctx, member, message)

    async def noteCommand(self, ctx, member, message):
        memberDB = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member.id})
        caseId = await get_next_num(self.bot.mdb['properties'], 'caseId')
        if memberDB is None:
            memberDB = {"server": ctx.interaction.guild_id, "user": member.id, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)
        case = Case(caseId, CaseType.NOTE, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.interaction.user.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.guild.id, "user": member.id}, {"$set": memberDB}, upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.respond(embed=embed)


def setup(bot):
    log.info("[Admin] Note")
    bot.add_cog(Note(bot))
