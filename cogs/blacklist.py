import typing
import discord
from discord import Permissions
from discord.ext import commands
from utils import logger
from utils import globals as GG
from DBService import DBService

log = logger.logger

TERMS = []
GREYS = []
CHECKS = [' ', ',', '.', '!', '?', None, '"', '\'', '(', ')', '{', '}', '[', ']', '_', '-', ':', '|', '*']


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, *, args):
        DBService.exec(
            "INSERT INTO Terms (Guild, Term) VALUES (" + str(ctx.guild.id) + ",'" + str(args) + "')")
        GG.TERMS.append(int(ctx.guild.id))
        await ctx.send(f"{args} was added to the term blacklist.")

    @commands.command(aliases=['greylist','graylist'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def greyblacklist(self, ctx, *, args):
        DBService.exec(
            "INSERT INTO Grey (Guild, Term) VALUES (" + str(ctx.guild.id) + ",'" + str(args) + "')")
        GG.GREYS.append(int(ctx.guild.id))
        await ctx.send(f"{args} was added to the term blacklist.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx, *, args):
        DBService.exec(
            "DELETE FROM Terms WHERE Guild = " + str(ctx.guild.id) + " AND Term = '" + str(args) + "'")
        GG.TERMS.remove(int(ctx.guild.id))
        await ctx.send(f"{args} was delete from the term blacklist.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def greywhitelist(self, ctx, *, args):
        DBService.exec(
            "DELETE FROM Grey WHERE Guild = " + str(ctx.guild.id) + " AND Term = '" + str(args) + "'")
        GG.GREYS.remove(int(ctx.guild.id))
        await ctx.send(f"{args} was delete from the term blacklist.")

    @commands.command(hidden=True)
    @commands.guild_only()
    async def blacklisted(self, ctx):
        TERMS = DBService.exec("SELECT Term FROM TERMS WHERE Guild = " + str(ctx.guild.id) + "").fetchall()
        TERMS = [''.join(i) for i in TERMS]
        em = discord.Embed()
        string = ""
        for x in TERMS:
            string += f"{x}\n"
        em.add_field(name="Blacklisted words", value=string)
        await ctx.send(embed=em)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def greylisted(self, ctx):
        TERMS = DBService.exec("SELECT Term FROM Grey WHERE Guild = " + str(ctx.guild.id) + "").fetchall()
        TERMS = [''.join(i) for i in TERMS]
        em = discord.Embed()
        string = ""
        for x in TERMS:
            string += f"{x}\n"
        em.add_field(name="Greylisted words", value=string)
        await ctx.send(embed=em)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != 602774912595263490 and message.author.id != 109133673172828160:
            if message.guild.id in GG.GREYS:
                GREYS = DBService.exec("SELECT Term FROM Grey WHERE Guild = " + str(
                    message.guild.id) + "").fetchall()
                GREYS = [''.join(i) for i in GREYS]
                for x in GREYS:
                    if message.content.find(x) != -1:
                        nextBool, previousBool = await self.checkMessage(message, x)

                        if previousBool and nextBool:
                            await self.bot.get_channel(603627784849326120).send(
                                f"{message.author.display_name} ({message.author.mention}) used a greylisted term in {message.channel.mention}.\nThe message: ```{message.content}```")
                            await message.delete()
                            break
            if message.guild.id in GG.TERMS:
                TERMS = DBService.exec("SELECT Term FROM TERMS WHERE Guild = " + str(
                    message.guild.id) + "").fetchall()
                TERMS = [''.join(i) for i in TERMS]
                for x in TERMS:
                    if message.content.find(x) != -1:
                        nextBool, previousBool = await self.checkMessage(message, x)

                        if previousBool and nextBool:
                            await self.bot.get_channel(603627784849326120).send(
                                f"{message.author.display_name} ({message.author.mention}) used a blacklisted term in {message.channel.mention}.\nThe message: ```{message.content}```")
                            if message.author.dm_channel is not None:
                                DM = message.author.dm_channel
                            else:
                                DM = await message.author.create_dm()
                            try:
                                await DM.send(
                                    f"Hey, your post was [redacted], because you used a blacklisted term: ``{x}``, watch your language. If you think this is an error and/or the term should be whitelisted, please contact a member of staff.\nYour message for the sake of completion: ```{message.content}```")
                            except discord.Forbidden:
                                await self.bot.get_channel(message.channel.id).send(
                                    f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")
                            await message.delete()
                            break

    async def checkMessage(self, message, x):
        start = message.content.find(x)
        if start != 0:
            previousChar = start - 1
            previousChar = message.content[previousChar]
        else:
            previousChar = None
        nextChar = start + int(len(x))
        if nextChar != None:
            try:
                nextChar = message.content[nextChar]
            except IndexError:
                nextChar = None
        else:
            nextChar = None
        nextBool = False
        previousBool = False
        for y in CHECKS:
            if y == nextChar:
                nextBool = True
            if y == previousChar:
                previousBool = True
        return nextBool, previousBool


def setup(bot):
    log.info("Loading Blacklist Terms Filter Cog...")
    bot.add_cog(Blacklist(bot))
