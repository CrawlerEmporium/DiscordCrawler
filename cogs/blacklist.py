import json
import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle

from crawler_utilities.handlers import logger
from utils import globals as GG
from crawler_utilities.utils.functions import try_delete

log = logger.logger

CHECKS = [' ', ',', '.', '!', '?', None, '"', '\'', '(', ')', '{', '}', '[', ']', '_', '-', ':', '|', '*', '~', '\n']


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
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
        GG.GREYLIST, GG.GREYGUILDS = await GG.fillGreyList(GG.GREYLIST, GG.GREYGUILDS)
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
            if TERMS is not None:
                for x in TERMS:
                    string += f"{x['term']}\n"
            else:
                string = "No blacklisted words on the server yet."
            em.add_field(name="Blacklisted words", value=string)
            await DM.send(embed=em)
        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I tried DMing you, but you either blocked me, or you don't allow DM's")
        await try_delete(ctx.message)

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
            if TERMS is not None:
                for x in TERMS:
                    string += f"{x['term']}\n"
            else:
                string = "No greylisted words on the server yet."
            em.add_field(name="Greylisted words", value=string)
            await DM.send(embed=em)
        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I tried DMing you, but you either blocked me, or you don't allow DM's")
        await try_delete(ctx.message)

    @commands.Cog.listener()
    async def on_button_click(self, res):
        if res.guild.id in GG.GREYGUILDS or res.guild.id in GG.GUILDS:
            if res.channel.id in GG.CHANNEL:
                if res.component.label == "Reject":
                    msg = res.message
                    embed = msg.embeds[0]
                    msgID = 0
                    channelID = 0
                    i = 0
                    for field in embed.fields:
                        if field.name == "MSGID":
                            msgID = field.value
                            embed.remove_field(i)
                        i += 1
                    i = 0
                    for field in embed.fields:
                        if field.name == "CHANNELID":
                            channelID = field.value
                            embed.remove_field(i)
                        i += 1
                    if channelID != 0 and msgID != 0:
                        try:
                            channel = await self.bot.fetch_channel(channelID)
                            message = await channel.fetch_message(msgID)
                            await message.delete()
                            embed.set_footer(text=f"Message was removed by {res.user.display_name}.")
                            await msg.edit(embed=embed, components=[])
                        except:
                            embed.set_footer(text="Couldn't find message, probably already deleted.")
                            await msg.edit(embed=embed, components=[])

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.checkForListedTerms(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, message):
        await self.checkForListedTerms(message)

    async def checkForListedTerms(self, message):
        if message.author.id != 602774912595263490:  # if not bot
            if message.guild is not None and message.guild.id in GG.GREYGUILDS:
                termsForGuild = [guild['terms'] for guild in GG.GREYLIST if guild['guild'] == message.guild.id][0]
                for term in termsForGuild:
                    if message.content.lower().find(term.lower()) != -1:
                        nextBool, previousBool = await self.checkMessage(message, term)

                        if previousBool and nextBool:
                            delivery_channel = await GG.MDB['channelinfo'].find_one(
                                {"guild": message.guild.id, "type": "BLACKLIST"})
                            if delivery_channel is not None:
                                delivery_channel = await self.bot.fetch_channel(delivery_channel['channel'])
                                return await delivery_channel.send(embed=await self.createEmbed(message, "greylisted", term),
                                                            components=[Button(style=ButtonStyle.red, label="Reject")])
                            else:
                                break
            if message.guild is not None and message.guild.id in GG.GUILDS:
                termsForGuild = [guild['terms'] for guild in GG.BLACKLIST if guild['guild'] == message.guild.id][0]
                for term in termsForGuild:
                    if message.content.lower().find(term.lower()) != -1:
                        nextBool, previousBool = await self.checkMessage(message, term)

                        if previousBool and nextBool:
                            delivery_channel = await GG.MDB['channelinfo'].find_one(
                                {"guild": message.guild.id, "type": "BLACKLIST"})
                            if delivery_channel is not None:
                                delivery_channel = await self.bot.fetch_channel(delivery_channel['channel'])
                                await delivery_channel.send(embed=await self.createEmbed(message, "blacklisted", term))
                            else:
                                break
                            await message.delete()
                            if message.author.dm_channel is not None:
                                DM = message.author.dm_channel
                            else:
                                DM = await message.author.create_dm()
                            try:
                                await DM.send(
                                    f"Hey, your post was [redacted], because you used a blacklisted term: ``{term}``, watch your language. If you think this is an error and/or the term should be whitelisted, please contact a member of staff.\nYour message for the sake of completion: ```{message.content}```")
                            except discord.Forbidden:
                                await delivery_channel.send(
                                    f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")

                            break


    async def createEmbed(self, message, type, term):
        embed = discord.Embed(title=f"{type.title()} word detected!",
                              description=f"```{message.content[:1020]}```")
        embed.add_field(name="Who", value=f"{message.author.display_name} ({message.author.mention})")
        embed.add_field(name="Where", value=f"[Here]({message.jump_url}) in {message.channel.mention}")
        embed.add_field(name=f"{type.title()} term", value=f"{term}")
        if type != 'blacklisted':
            embed.add_field(name="MSGID", value=f"{message.id}")
            embed.add_field(name="CHANNELID", value=f"{message.channel.id}")
        return embed

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
