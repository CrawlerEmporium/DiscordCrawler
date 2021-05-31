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
        await self.caseCommand(ctx, caseId)

    @case.command(name='close')
    @commands.guild_only()
    @GG.is_staff()
    async def close_case(self, ctx, caseId: int, *, message=""):
        await self.closeCaseCommand(ctx, caseId, message)

    @case.command(name='update')
    @commands.guild_only()
    @GG.is_staff()
    async def update_case(self, ctx, caseId: int, *, message=""):
        await self.updateCaseCommand(ctx, caseId, message)

    @case.command(name='list')
    @commands.guild_only()
    @GG.is_staff()
    async def list_case(self, ctx, member: typing.Optional[discord.Member] = None):
        await self.listCaseCommand(ctx, member)


    # @cog_ext.cog_subcommand(base="case", name="check", description="Checks a case", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="caseId", description="The id of the case you want to check.", option_type=4,
    #                   required=True)
    # ])
    # @GG.is_staff()
    # async def caseSlash(self, ctx, caseId: int = 0):
    #     await self.caseCommand(ctx, caseId)
    #
    # @cog_ext.cog_subcommand(base="case", name="close", description="Closes a case", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="caseId", description="The id of the case you want to close.", option_type=4,
    #                   required=True)
    # ])
    # @GG.is_staff()
    # async def closeCaseSlash(self, ctx, caseId: int, *, message=""):
    #     await self.closeCaseCommand(ctx, caseId, message)
    #
    # @cog_ext.cog_subcommand(base="case", name="update", description="Updates a case", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="caseId", description="The id of the case you want to update.", option_type=4,
    #                   required=True)
    # ])
    # @GG.is_staff()
    # async def updateCaseSlash(self, ctx, caseId: int, *, message=""):
    #     await self.updateCaseCommand(ctx, caseId, message)
    #
    # @cog_ext.cog_subcommand(base="case", name="list", description="Lists all cases for an user", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="user", description="The user of which you want to check all cases.", option_type=6,
    #                   required=False)
    # ])
    # @GG.is_staff()
    # async def listCaseSlash(self, ctx, member: typing.Optional[discord.Member]):
    #     await self.listCaseCommand(ctx, member)

    async def closeCaseCommand(self, ctx, caseId, message):
        caseId = await self.validId(caseId, ctx)
        if caseId == 0:
            return

        case = await GG.MDB.cases.find_one({"caseId": caseId})
        if case is not None:
            msg = case['message']
            msg += f"\nCLOSED - {message}"
            await GG.MDB.cases.update_one({"caseId": caseId}, {"$set": {"status": CaseStatus.CLOSED, "message": msg}},
                                          upsert=False)
            await ctx.send(f"Case ``{caseId}`` was closed.")
        else:
            await ctx.send(f"There is no case with id: ``{caseId}``")

    async def updateCaseCommand(self, ctx, caseId, message):
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

    async def listCaseCommand(self, ctx, member):
        if member is None:
            return await ctx.send("Member can't be none. Proper command to use ``$case list [memberId]``")

        user = member
        guild = ctx.message.guild
        await guild.chunk()
        avi = user.avatar_url

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

        em.set_thumbnail(url=avi or None)
        await ctx.send(embed=em)

    async def caseCommand(self, ctx, caseId):
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
            await ctx.send(embed=embed)

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
