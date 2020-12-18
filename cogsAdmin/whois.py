import discord
import typing

import utils.globals as GG
from discord.ext import commands

from cogsAdmin.models.caseType import CaseType
from utils import logger

log = logger.logger


class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['whois'])
    @commands.guild_only()
    @GG.is_staff()
    async def check(self, ctx, member: typing.Optional[discord.Member] = None):
        """[STAFF ONLY]"""
        if member is None:
            return await ctx.send("Member can't be none.``")
        else:
            user = member
            guild = ctx.message.guild
            await guild.chunk()
            avi = user.avatar_url
            roles = sorted(user.roles, key=lambda r: r.position)
            rolenames = ', '.join([r.name for r in roles if r != '@everyone']) or 'None'
            time = ctx.message.created_at
            desc = f'{user.name} is currently in {user.status} mode.'
            try:
                member_number = sorted(guild.members, key=lambda m: m.joined_at).index(user) + 1
            except TypeError:
                member_number = "Unknown"
            em = discord.Embed(color=user.color, description=desc, timestamp=time)

            em.add_field(name='Name', value=user.name),
            em.add_field(name="Display Name", value=member.display_name),
            em.add_field(name='Member Number', value=str(member_number)),

            em.add_field(name='Account Created', value=user.created_at.__format__('%A, %B %d, %Y')),
            em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %B %d, %Y')),
            em.add_field(name='Roles', value=rolenames)

            cases = await GG.MDB.members.find_one({"server": guild.id, "user": user.id})
            notes = []
            warnings = []
            kicks = []
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


def setup(bot):
    log.info("[Admin] Whois")
    bot.add_cog(Whois(bot))
