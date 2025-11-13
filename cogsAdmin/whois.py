from datetime import datetime

import discord

from discord import slash_command, Option

from discord.ext import commands
from cogsAdmin.models.caseType import CaseType

from utils import globals as GG
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs

log = GG.log


class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "whois"

    @slash_command(**get_command_kwargs(cogName, "whois"))
    @commands.guild_only()
    async def whois(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, "whois.member"))):
        await ctx.defer()
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        guild = ctx.interaction.guild
        if member is None or member is discord.User:
            return await ctx.respond("Member is no longer in this server.")

        cases = await GG.MDB.members.find_one({"server": guild.id, "user": member.id})
        adminString, noteString, warningString = await getCaseStrings(cases)

        em = await getMemberEmbed(adminString, guild, noteString, member, warningString)
        await ctx.respond(embed=em)

    @commands.user_command(name="Staff: User Check")
    @commands.guild_only()
    async def user_whois_test(self, ctx, member: discord.Member):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        guild = ctx.guild
        if member is None or member is discord.User:
            return await ctx.respond("Member is no longer in this server.")

        cases = await GG.MDB.members.find_one({"server": guild.id, "user": member.id})
        adminString, noteString, warningString = await getCaseStrings(cases)

        em = await getMemberEmbed(adminString, guild, noteString, member, warningString)

        return await ctx.respond(embed=em, ephemeral=True)


async def getMemberEmbed(adminString, guild, noteString, user, warningString):
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


async def getCaseStrings(cases):
    notes = []
    warnings = []
    mutes = []
    tempbans = []
    bans = []

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
