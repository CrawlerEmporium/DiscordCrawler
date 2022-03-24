from datetime import datetime

import discord
from discord import slash_command, Option

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

    @slash_command()
    async def note(self, ctx, member: Option(discord.Member, "To which member do you want to attach a note?"), message: Option(str, "What should the note be?")):
        """[STAFF] Adds a note to the member"""
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.noteCommand(ctx, member, message)

    async def noteCommand(self, ctx, member, message):
        try:
            member = int(member)
        except ValueError:
            try:
                ic = await ctx.interaction.guild.fetch_member(602779023151595546)
            except discord.HTTPException:
                ic = None
            if ic is not None:
                return await ctx.respond(f"{member} is not a userid (or username). Seeing that you have <@602779023151595546> in this server, it might be possible you are mixing commands.")
            else:
                return await ctx.respond(f"{member} is not a userid (or username).")
        if ctx.interaction.guild.get_member(member) is None:
            return await ctx.send("Member wasn't found on the server. Inserting note as a general snowflake.\n\nPlease check if this is actually a member, it might be a channel/message id.")
        memberDB = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member})
        caseId = await get_next_num(self.bot.mdb['properties'], 'caseId')
        if memberDB is None:
            memberDB = {"server": ctx.interaction.guild_id, "user": member, "caseIds": [caseId]}
        else:
            memberDB['caseIds'].append(caseId)
        case = Case(caseId, CaseType.NOTE, CaseStatus.OPEN, message, datetime.now(), member, ctx.interaction.author.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.guild.id, "user": member}, {"$set": memberDB}, upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.respond(embed=embed)


def setup(bot):
    log.info("[Admin] Note")
    bot.add_cog(Note(bot))
