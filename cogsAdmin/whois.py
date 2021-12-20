from datetime import datetime

import discord
import typing

import utils.globals as GG
from discord.ext import commands
from cogsAdmin.models.caseType import CaseType

from crawler_utilities.handlers import logger

log = logger.logger


class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['check'])
    @commands.guild_only()
    @GG.is_staff()
    async def whois(self, ctx, member: typing.Union[discord.Member, int] = None):
        """[STAFF ONLY]"""
        if member is None:
            return await ctx.send("Member can't be none.")
        else:
            notes = []
            warnings = []
            mutes = []
            tempbans = []
            bans = []
            cases = None

            if type(member) is discord.Member:
                user = member
                guild = ctx.message.guild
                cases = await GG.MDB.members.find_one({"server": guild.id, "user": user.id})
            if type(member) is int:
                user = member
                cases = await GG.MDB.members.find_one({"server": ctx.message.guild.id, "user": user})
                if cases is None:
                    return await ctx.send("Member no is longer on this server, and has no notes attached to it.")

            adminString, noteString, warningString = await getCaseStrings(bans, cases, mutes, notes, tempbans, warnings)

            if type(member) is discord.Member:
                em = await getMemberEmbed(adminString, guild, noteString, user, warningString)
                await ctx.send(embed=em)

            if type(member) is int:
                em = discord.Embed()
                if noteString != "":
                    em.add_field(name='Notes', value=noteString, inline=False)
                if warningString != "":
                    em.add_field(name='Warnings', value=warningString, inline=False)
                if adminString != "":
                    em.add_field(name='Administration', value=adminString, inline=False)
                await ctx.send(content="Member no is longer on this server, but has prior notes attached to it.", embed=em)


async def getMemberEmbed(adminString, guild, noteString, user, warningString):
    await guild.chunk()
    roles = sorted(user.roles, key=lambda r: r.position)
    rolenames = ', '.join([r.name for r in roles if r != '@everyone']) or 'None'
    desc = f'{user.name} is currently in {user.status} mode.'
    try:
        member_number = sorted(guild.members, key=lambda m: m.joined_at).index(user) + 1
    except TypeError:
        member_number = "Unknown"
    em = discord.Embed(color=user.color, description=desc, timestamp=datetime.now())
    em.add_field(name='Name', value=user.name),
    em.add_field(name="Display Name", value=user.display_name),
    em.add_field(name='Member Number', value=str(member_number)),
    em.add_field(name='Account Created', value=user.created_at.__format__('%A, %B %d, %Y')),
    em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %B %d, %Y')),
    em.add_field(name='Roles', value=rolenames)
    if noteString != "":
        em.add_field(name='Notes', value=noteString, inline=False)
    if warningString != "":
        em.add_field(name='Warnings', value=warningString, inline=False)
    if adminString != "":
        em.add_field(name='Administration', value=adminString, inline=False)
    if user.display_avatar.url is not None:
        em.set_thumbnail(url=user.display_avatar.url)
    return em


async def getCaseStrings(bans, cases, mutes, notes, tempbans, warnings):
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
    warningString = ""
    if len(warnings) > 0:
        for note in warnings:
            warningString += f"{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    adminString = ""
    if len(mutes) > 0:
        for note in mutes:
            adminString += f"[**TIME-OUTS**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    if len(tempbans) > 0:
        for note in tempbans:
            adminString += f"[**TEMP-BANNED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    if len(bans) > 0:
        for note in bans:
            adminString += f"[**BANNED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    noteString = ""
    if len(notes) > 0:
        for note in notes:
            noteString += f"{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    return adminString, noteString, warningString

def setup(bot):
    log.info("[Admin] Whois")
    bot.add_cog(Whois(bot))
