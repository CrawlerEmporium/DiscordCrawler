import discord
import typing

import utils.globals as GG
from discord.ext import commands

from crawler_utilities.handlers import logger
from tempFiles.whois import getCaseStrings, getMemberEmbed

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


def setup(bot):
    log.info("[Admin] Whois")
    bot.add_cog(Whois(bot))
