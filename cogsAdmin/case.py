import discord
import typing

from discord import Option, SlashCommandGroup

import utils.globals as GG
from discord.ext import commands

from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from crawler_utilities.handlers import logger

log = logger.logger


class Case(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    case = SlashCommandGroup("case", "All case commands")

    @case.command(name='check')
    async def check(self, ctx, caseId: Option(int, "Which case do you want check?")):
        """[STAFF] Checks a case"""
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.caseCommand(ctx, caseId)

    @case.command(name='close')
    async def close(self, ctx, caseId: Option(int, "Which case do you want check?"), message: Option(str, "Optional note for closing the case") = ""):
        """[STAFF] Closes a case"""
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.closeCaseCommand(ctx, caseId, message)

    @case.command(name='update')
    async def update(self, ctx, caseId: Option(int, "Which case do you want check?"), message: Option(str, "Optional note for updating the case") = ""):
        """[STAFF] Updates a case"""
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.updateCaseCommand(ctx, caseId, message)

    @case.command(name='list')
    async def list(self, ctx, member: Option(discord.Member, "Whose cases do you want to see?")):
        """[STAFF] Lists all cases for a member"""
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.listCaseCommand(ctx, member)

    @staticmethod
    async def closeCaseCommand(ctx, caseId, message):
        case = await GG.MDB.cases.find_one({"caseId": f"{caseId}"})
        if case is not None:
            msg = case['message']
            msg += f"\nCLOSED - {message}"
            await GG.MDB.cases.update_one({"caseId": f"{caseId}"}, {"$set": {"status": CaseStatus.CLOSED, "message": msg}},
                                          upsert=False)
            await ctx.respond(f"Case ``{caseId}`` was closed.")
        else:
            await ctx.respond(f"There is no case with id: ``{caseId}``")

    @staticmethod
    async def updateCaseCommand(ctx, caseId, message):
        case = await GG.MDB.cases.find_one({"caseId": f"{caseId}"})
        if case is not None:
            msg = case['message']
            msg += f"\nUPDATE - {message}"
            await GG.MDB.cases.update_one({"caseId": f"{caseId}"}, {"$set": {"message": msg}}, upsert=False)
            await ctx.respond(f"Case ``{caseId}`` was updated.")
        else:
            await ctx.respond(f"There is no case with id: ``{caseId}``")

    @staticmethod
    async def listCaseCommand(ctx, user):
        guild = ctx.interaction.guild
        await guild.chunk()
        avi = user.display_avatar.url

        cases = await GG.MDB.members.find_one({"server": guild.id, "user": user.id})
        notes = []
        warnings = []
        mutes = []
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
                    elif case['caseType'] == CaseType.MUTE:
                        mutes.append(case)
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
        if len(mutes) > 0:
            for note in mutes:
                adminString += f"[**MUTED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
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

        em.set_thumbnail(url=avi)
        await ctx.respond(embed=em)

    @staticmethod
    async def caseCommand(ctx, caseId):
        case = await GG.MDB.cases.find_one({"caseId": f"{caseId}"})
        if case is not None:
            embed = discord.Embed()
            embed.title = f"Case {case['caseId']}"
            if case['caseType'] == CaseType.NOTE:
                embed.title += " - Note"
            elif case['caseType'] == CaseType.WARNING:
                embed.title += " - Warning"
            elif case['caseType'] == CaseType.MUTE:
                embed.title += " - Mute"
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
            await ctx.respond(embed=embed)


def setup(bot):
    log.info("[Admin] Case")
    bot.add_cog(Case(bot))
