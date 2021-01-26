import discord
import typing

import utils.globals as GG
from discord.ext import commands

from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import logger

log = logger.logger


class Case(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @GG.is_staff()
    async def case(self, ctx, caseId: int = 0):
        caseId = await self.validId(caseId, ctx)
        if caseId == 0:
            return

        case = await GG.MDB.cases.find_one({"caseId": caseId})
        if case is not None:
            embed = discord.Embed()
            embed.title = f"Case {case['caseId']}"
            if case['caseType'] == CaseType.NOTE:
                embed.title += " - Note"
            elif case['caseType'] == CaseType.WARNING:
                embed.title += " - Warning"
            elif case['caseType'] == CaseType.KICK:
                embed.title += " - Kick"
            elif case['caseType'] == CaseType.TEMPBAN:
                embed.title += " - Temp-Ban"
            elif case['caseType'] == CaseType.BAN:
                embed.title += " - Ban"
            embed.description = f"{case['message']}"
            embed.timestamp = case['date']
            if case['status'] == 0:
                embed.set_footer(text="Status: OPEN")
            if case['status'] == 1:
                embed.set_footer(text="Status: CLOSED")
            await ctx.send(embed=embed)

    @case.command(name='close')
    @commands.guild_only()
    @GG.is_staff()
    async def close_case(self, ctx, caseId: int, *, message=""):
        caseId = await self.validId(caseId, ctx)
        if caseId == 0:
            return

        case = await GG.MDB.cases.find_one({"caseId": caseId})
        if case is not None:
            msg = case['message']
            msg += f"\nCLOSED - {message}"
            await GG.MDB.cases.update_one({"caseId": caseId}, {"$set": {"status": CaseStatus.CLOSED, "message": msg}}, upsert=False)
            await ctx.send(f"Case ``{caseId}`` was closed.")
        else:
            await ctx.send(f"There is no case with id: ``{caseId}``")

    @case.command(name='update')
    @commands.guild_only()
    @GG.is_staff()
    async def update_case(self, ctx, caseId: int, *, message=""):
        caseId = await self.validId(caseId, ctx)
        if caseId == 0:
            return

        case = await GG.MDB.cases.find_one({"caseId": caseId})
        if case is not None:
            msg = case['message']
            msg += f"\nUPDATE - {message}"
            await GG.MDB.cases.update_one({"caseId": caseId}, {"$set": {"message": msg}}, upsert=False)
            await ctx.send(f"Case ``{caseId}`` was updated.")
        else:
            await ctx.send(f"There is no case with id: ``{caseId}``")

    @case.command(name='list')
    @commands.guild_only()
    @GG.is_staff()
    async def list_case(self, ctx, member: typing.Optional[discord.Member] = None):
        if member is None:
            return await ctx.send("Member can't be none. Proper command to use ``$case list [memberId]``")

        user = member
        guild = ctx.message.guild
        await guild.chunk()
        avi = user.avatar_url

        cases = await GG.MDB.members.find_one({"server": guild.id, "user": user.id})
        notes = []
        warnings = []
        kicks = []
        tempbans = []
        bans = []
        em = discord.Embed(color=user.color)

        if cases is not None:
            for x in cases['caseIds']:
                case = await GG.MDB.cases.find_one({"caseId": x})
                if case is not None:
                    if case['caseType'] == CaseType.NOTE:
                        notes.append(case)
                    elif case['caseType'] == CaseType.WARNING:
                        warnings.append(case)
                    elif case['caseType'] == CaseType.KICK:
                        kicks.append(case)
                    elif case['caseType'] == CaseType.TEMPBAN:
                        tempbans.append(case)
                    elif case['caseType'] == CaseType.BAN:
                        bans.append(case)

        if len(warnings) > 0:
            warningString = ""
            for note in warnings:
                warningString += f"{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
            em.add_field(name='Warnings', value=warningString, inline=False)

        adminString = ""
        if len(kicks) > 0:
            for note in kicks:
                adminString += f"[**KICKED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
        if len(tempbans) > 0:
            for note in tempbans:
                adminString += f"[**TEMP-BANNED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
        if len(bans) > 0:
            for note in bans:
                adminString += f"[**BANNED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
        if adminString != "":
            em.add_field(name='Administration', value=adminString, inline=False)

        if len(notes) > 0:
            noteString = ""
            for note in notes:
                noteString += f"{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
            em.add_field(name='Notes', value=noteString, inline=False)

        em.set_thumbnail(url=avi or None)
        await ctx.send(embed=em)

    async def validId(self, caseId, ctx):
        if caseId is None:
            await ctx.send("Please give me a valid case Id.")
            caseId = 0
        try:
            caseId = int(caseId)
        except ValueError:
            await ctx.send("Please give me a valid case Id.")
            caseId = 0
        return caseId


def setup(bot):
    log.info("[Admin] Case")
    bot.add_cog(Case(bot))
