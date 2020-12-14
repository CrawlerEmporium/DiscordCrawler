import json
import discord
from discord.ext import commands
from utils import logger
from utils import globals as GG

log = logger.logger

CHECKS = [' ', ',', '.', '!', '?', None, '"', '\'', '(', ')', '{', '}', '[', ']', '_', '-', ':', '|', '*', '~']

class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def refillLists(self, ctx):
        GG.BLACKLIST = "["
        TERMDB = await GG.MDB['blacklist'].find({}).to_list(length=None)
        guildList = []
        for x in TERMDB:
            if x['guild'] not in guildList:
                guildList.append(x['guild'])
        for y in guildList:
            guildTermList = []
            for x in TERMDB:
                if y == x['guild']:
                    guildTermList.append(x['term'])
            termList = ""
            for x in guildTermList:
                termList += f'"{x}",'
            termList = termList[:-1]
            guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
            GG.BLACKLIST += guildTerms
        GG.BLACKLIST = GG.BLACKLIST[:-1]
        GG.BLACKLIST += "]"
        GG.BLACKLIST = json.loads(GG.BLACKLIST)
        for x in GG.BLACKLIST:
            GG.GUILDS.append(x['guild'])

        GG.GREYLIST = "["
        TERMDB = await GG.MDB['greylist'].find({}).to_list(length=None)
        guildList = []
        for x in TERMDB:
            if x['guild'] not in guildList:
                guildList.append(x['guild'])
        for y in guildList:
            guildTermList = []
            for x in TERMDB:
                if y == x['guild']:
                    guildTermList.append(x['term'])
            termList = ""
            for x in guildTermList:
                termList += f'"{x}",'
            termList = termList[:-1]
            guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
            GG.GREYLIST += guildTerms
        GG.GREYLIST = GG.GREYLIST[:-1]
        GG.GREYLIST += "]"
        GG.GREYLIST = json.loads(GG.GREYLIST)
        for x in GG.GREYLIST:
            GG.GREYGUILDS.append(x['guild'])

    @commands.command(aliases=['bl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, *, args):
        await GG.MDB['blacklist'].insert_one({"guild": ctx.guild.id, "term": args})
        GG.BLACKLIST, GG.GUILDS = await GG.fillBlackList(GG.BLACKLIST, GG.GUILDS)
        await ctx.send(f"{args} was added to the term blacklist.")

    @commands.command(aliases=['greylist', 'graylist', 'grayblacklist', 'gbl', 'gl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def greyblacklist(self, ctx, *, args):
        await GG.MDB['greylist'].insert_one({"guild": ctx.guild.id, "term": args})
        GG.BLACKLIST, GG.GUILDS = await GG.fillGreyList(GG.BLACKLIST, GG.GUILDS)
        await ctx.send(f"{args} was added to the term greylist.")

    @commands.command(aliases=['wl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx, *, args):
        await GG.MDB['blacklist'].delete_one({"guild": ctx.guild.id, "term": args})
        GG.BLACKLIST, GG.GUILDS = await GG.fillBlackList(GG.BLACKLIST, GG.GUILDS)
        await ctx.send(f"{args} was deleted from the term blacklist.")

    @commands.command(aliases=['graywhitelist', 'gwl'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def greywhitelist(self, ctx, *, args):
        await GG.MDB['greylist'].delete_one({"guild": ctx.guild.id, "term": args})
        GG.GREYLIST, GG.GREYGUILDS = await GG.fillGreyList(GG.GREYLIST, GG.GREYGUILDS)
        await ctx.send(f"{args} was deleted from the term greylist.")

    @commands.command()
    @commands.guild_only()
    async def blacklisted(self, ctx):
        TERMS = await GG.MDB.blacklist.find({"guild": ctx.guild.id}).to_list(length=None)
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
            await ctx.send(f"{ctx.author.mention} I tried DMing you, but you either blocked me, or you don't allow DM's")
        await ctx.message.delete()

    @commands.command(aliases=['graylisted'])
    @commands.guild_only()
    async def greylisted(self, ctx):
        TERMS = await GG.MDB.greylist.find({"guild": ctx.guild.id}).to_list(length=None)
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
        if message.author.id != 602774912595263490 and message.author.id != 109133673172828160 and message.author.id != 95486109852631040:
            if message.guild.id in GG.GREYGUILDS:
                for x in GG.GREYLIST:
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
            if message.guild.id in GG.GUILDS:
                for x in GG.BLACKLIST:
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
                                    await message.delete()
                                    if message.author.dm_channel is not None:
                                        DM = message.author.dm_channel
                                    else:
                                        DM = await message.author.create_dm()
                                    try:
                                        await DM.send(
                                            f"Hey, your post was [redacted], because you used a blacklisted term: ``{y}``, watch your language. If you think this is an error and/or the term should be whitelisted, please contact a member of staff.\nYour message for the sake of completion: ```{message.content}```")
                                    except discord.Forbidden:
                                        if message.guild.id == 154312731879669770:
                                            await self.bot.get_channel(603627784849326120).send(
                                                f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")
                                        elif message.guild.id == 584842413135101990:
                                            await self.bot.get_channel(604728578801795074).send(
                                                f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")
                                        else:
                                            await self.bot.get_channel(message.channel.id).send(
                                                f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")
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
    log.info("[Cog] Blacklist Terms Filter")
    bot.add_cog(Blacklist(bot))
