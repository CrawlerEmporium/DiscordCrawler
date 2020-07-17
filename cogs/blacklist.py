import json
import typing
import discord
from discord import Permissions
from discord.ext import commands
from utils import logger
from utils import globals as GG
from DBService import DBService

log = logger.logger

CHECKS = [' ', ',', '.', '!', '?', None, '"', '\'', '(', ')', '{', '}', '[', ']', '_', '-', ':', '|', '*', '~']


def fillBlackList(BLACKLIST, GUILDS):
    BLACKLIST = "["
    TERMDB = DBService.exec("SELECT Guild, Term FROM Terms").fetchall()
    guildList = []
    for x in TERMDB:
        if x[0] not in guildList:
            guildList.append(x[0])
    for y in guildList:
        guildTermList = []
        for x in TERMDB:
            if y == x[0]:
                guildTermList.append(x[1])
        termList = ""
        for x in guildTermList:
            termList += f'"{x}",'
        termList = termList[:-1]
        guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
        BLACKLIST += guildTerms
    BLACKLIST = BLACKLIST[:-1]
    BLACKLIST += "]"
    BLACKLIST = json.loads(BLACKLIST)
    for x in BLACKLIST:
        GUILDS.append(x['guild'])
    return BLACKLIST, GUILDS


def fillGreyList(GREYLIST, GREYGUILDS):
    GREYLIST = "["
    TERMDB = DBService.exec("SELECT Guild, Term FROM Grey").fetchall()
    guildList = []
    for x in TERMDB:
        if x[0] not in guildList:
            guildList.append(x[0])
    for y in guildList:
        guildTermList = []
        for x in TERMDB:
            if y == x[0]:
                guildTermList.append(x[1])
        termList = ""
        for x in guildTermList:
            termList += f'"{x}",'
        termList = termList[:-1]
        guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
        GREYLIST += guildTerms
    GREYLIST = GREYLIST[:-1]
    GREYLIST += "]"
    GREYLIST = json.loads(GREYLIST)
    for x in GREYLIST:
        GREYGUILDS.append(x['guild'])
    return GREYLIST, GREYGUILDS


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BLACKLIST = ""
        self.GREYLIST = ""
        self.GUILDS = []
        self.GREYGUILDS = []
        self.BLACKLIST, self.GUILDS = fillBlackList(self.BLACKLIST, self.GUILDS)
        self.GREYLIST, self.GREYGUILDS = fillGreyList(self.GREYLIST, self.GREYGUILDS)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def refillLists(self, ctx):
        self.BLACKLIST = "["
        TERMDB = DBService.exec("SELECT Guild, Term FROM Terms").fetchall()
        guildList = []
        for x in TERMDB:
            if x[0] not in guildList:
                guildList.append(x[0])
        for y in guildList:
            guildTermList = []
            for x in TERMDB:
                if y == x[0]:
                    guildTermList.append(x[1])
            termList = ""
            for x in guildTermList:
                termList += f'"{x}",'
            termList = termList[:-1]
            guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
            self.BLACKLIST += guildTerms
        self.BLACKLIST = self.BLACKLIST[:-1]
        self.BLACKLIST += "]"
        self.BLACKLIST = json.loads(self.BLACKLIST)
        for x in self.BLACKLIST:
            self.GUILDS.append(x['guild'])

        self.GREYLIST = "["
        TERMDB = DBService.exec("SELECT Guild, Term FROM Grey").fetchall()
        guildList = []
        for x in TERMDB:
            if x[0] not in guildList:
                guildList.append(x[0])
        for y in guildList:
            guildTermList = []
            for x in TERMDB:
                if y == x[0]:
                    guildTermList.append(x[1])
            termList = ""
            for x in guildTermList:
                termList += f'"{x}",'
            termList = termList[:-1]
            guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
            self.GREYLIST += guildTerms
        self.GREYLIST = self.GREYLIST[:-1]
        self.GREYLIST += "]"
        self.GREYLIST = json.loads(self.GREYLIST)
        for x in self.GREYLIST:
            self.GREYGUILDS.append(x['guild'])

    @commands.command(aliases=['bl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, *, args):
        DBService.exec(
            "INSERT INTO Terms (Guild, Term) VALUES (" + str(ctx.guild.id) + ",'" + str(args) + "')")
        self.BLACKLIST, self.GUILDS = fillBlackList(self.BLACKLIST, self.GUILDS)
        await ctx.send(f"{args} was added to the term blacklist.")

    @commands.command(aliases=['greylist', 'graylist', 'grayblacklist', 'gbl', 'gl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def greyblacklist(self, ctx, *, args):
        DBService.exec(
            "INSERT INTO Grey (Guild, Term) VALUES (" + str(ctx.guild.id) + ",'" + str(args) + "')")
        self.BLACKLIST, self.GUILDS = fillBlackList(self.BLACKLIST, self.GUILDS)
        await ctx.send(f"{args} was added to the term greylist.")

    @commands.command(aliases=['wl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx, *, args):
        DBService.exec(
            "DELETE FROM Terms WHERE Guild = " + str(ctx.guild.id) + " AND Term = '" + str(args) + "'")
        self.BLACKLIST, self.GUILDS = fillBlackList(self.BLACKLIST, self.GUILDS)
        await ctx.send(f"{args} was delete from the term blacklist.")

    @commands.command(aliases=['graywhitelist', 'gwl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def greywhitelist(self, ctx, *, args):
        DBService.exec(
            "DELETE FROM Grey WHERE Guild = " + str(ctx.guild.id) + " AND Term = '" + str(args) + "'")
        self.GREYLIST, self.GREYGUILDS = fillGreyList(self.GREYLIST, self.GREYGUILDS)
        await ctx.send(f"{args} was delete from the term greylist.")

    @commands.command()
    @commands.guild_only()
    async def blacklisted(self, ctx):
        TERMS = DBService.exec("SELECT Term FROM TERMS WHERE Guild = " + str(ctx.guild.id) + "").fetchall()
        TERMS = [''.join(i) for i in TERMS]
        if ctx.author.dm_channel is not None:
            DM = ctx.author.dm_channel
        else:
            DM = await ctx.author.create_dm()
        try:
            em = discord.Embed()
            string = ""
            for x in TERMS:
                string += f"{x}\n"
            em.add_field(name="Blacklisted words", value=string)
            await DM.send(embed=em)
        except discord.Forbidden:
            await ctx.send(f"I tried DMing you, but you either blocked me, or don't allow DM's")
        await ctx.message.delete()

    @commands.command(aliases=['graylisted'])
    @commands.guild_only()
    async def greylisted(self, ctx):
        TERMS = DBService.exec("SELECT Term FROM Grey WHERE Guild = " + str(ctx.guild.id) + "").fetchall()
        TERMS = [''.join(i) for i in TERMS]
        if ctx.author.dm_channel is not None:
            DM = ctx.author.dm_channel
        else:
            DM = await ctx.author.create_dm()
        try:
            em = discord.Embed()
            string = ""
            for x in TERMS:
                string += f"{x}\n"
            em.add_field(name="Greylisted words", value=string)
            await DM.send(embed=em)
        except discord.Forbidden:
            await ctx.send(f"I tried DMing you, but you either blocked me, or don't allow DM's")
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != 602774912595263490 and message.author.id != 109133673172828160:
            if message.guild.id in self.GREYGUILDS:
                for x in self.GREYLIST:
                    if x['guild'] == message.guild.id:
                        for y in x['terms']:
                            if message.content.lower().find(y.lower()) != -1:
                                nextBool, previousBool = await self.checkMessage(message, y)

                                if previousBool and nextBool:
                                    if message.guild.id == 154312731879669770:
                                        await self.bot.get_channel(603627784849326120).send(
                                            f"{message.author.display_name} ({message.author.mention}) used a greylisted term in {message.channel.mention}.\nThe message: ```{message.content}```")
                                    if message.guild.id == 584842413135101990:
                                        await self.bot.get_channel(604728578801795074).send(
                                            f"{message.author.display_name} ({message.author.mention}) used a greylisted term in {message.channel.mention}.\nThe message: ```{message.content}```")
                                    break
            if message.guild.id in self.GUILDS:
                for x in self.BLACKLIST:
                    if x['guild'] == message.guild.id:
                        for y in x['terms']:
                            if message.content.lower().find(y.lower()) != -1:
                                nextBool, previousBool = await self.checkMessage(message, y)

                                if previousBool and nextBool:
                                    if message.guild.id == 154312731879669770:
                                        await self.bot.get_channel(603627784849326120).send(
                                            f"{message.author.display_name} ({message.author.mention}) used a blacklisted term in {message.channel.mention}.\nThe message: ```{message.content}```")
                                    if message.guild.id == 584842413135101990:
                                        await self.bot.get_channel(604728578801795074).send(
                                            f"{message.author.display_name} ({message.author.mention}) used a blacklisted term in {message.channel.mention}.\nThe message: ```{message.content}```")
                                    if message.author.dm_channel is not None:
                                        DM = message.author.dm_channel
                                    else:
                                        DM = await message.author.create_dm()
                                    try:
                                        await DM.send(
                                            f"Hey, your post was [redacted], because you used a blacklisted term: ``{y}``, watch your language. If you think this is an error and/or the term should be whitelisted, please contact a member of staff.\nYour message for the sake of completion: ```{message.content}```")
                                    except discord.Forbidden:
                                        await self.bot.get_channel(message.channel.id).send(
                                            f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")
                                    await message.delete()
                                    break

    async def checkMessage(self, message, x):
        start = message.content.lower().find(x.lower())
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
