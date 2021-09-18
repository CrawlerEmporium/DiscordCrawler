import discord
from discord.ext import commands

from crawler_utilities.handlers import logger
from models.buttons.greylist import Greylist
from utils import globals as GG

log = logger.logger

CHECKS = [' ', ',', '.', '!', '?', None, '"', '\'', '(', ')', '{', '}', '[', ']', '_', '-', ':', '|', '*', '~', '\n']


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.checkForListedTerms(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, message):
        await self.checkForListedTerms(message)

    async def checkForListedTerms(self, message):
        if message.author.id != 602774912595263490:  # if not bot
            if isinstance(message.channel, discord.threads.Thread):
                if message.guild is not None and message.guild.id in GG.GREYGUILDS:
                    termsForGuild = [guild['terms'] for guild in GG.GREYLIST if guild['guild'] == message.guild.id][0]
                    for term in termsForGuild:
                        if message.content.lower().find(term.lower()) != -1:
                            nextBool, previousBool = await self.checkMessage(message, term)

                            if previousBool and nextBool:
                                delivery_channel = await GG.MDB['channelinfo'].find_one({"guild": message.guild.id, "type": "BLACKLIST"})
                                if delivery_channel is not None:
                                    delivery_channel = await self.bot.fetch_channel(delivery_channel['channel'])
                                    return await delivery_channel.send(embed=await self.createEmbed(message, "greylisted", term),
                                                                       view=Greylist(self.bot))
                                else:
                                    break
                if message.guild is not None and message.guild.id in GG.GUILDS:
                    termsForGuild = [guild['terms'] for guild in GG.BLACKLIST if guild['guild'] == message.guild.id][0]
                    for term in termsForGuild:
                        if message.content.lower().find(term.lower()) != -1:
                            nextBool, previousBool = await self.checkMessage(message, term)
                            if previousBool and nextBool:
                                delivery_channel = await GG.MDB['channelinfo'].find_one({"guild": message.guild.id, "type": "BLACKLIST"})
                                if delivery_channel is not None:
                                    delivery_channel = await self.bot.fetch_channel(delivery_channel['channel'])
                                    await delivery_channel.send(embed=await self.createEmbed(message, "blacklisted", term))
                                else:
                                    pass
                                await message.delete()
                                if message.author.dm_channel is not None:
                                    DM = message.author.dm_channel
                                else:
                                    DM = await message.author.create_dm()
                                try:
                                    await DM.send(f"Hey, your post was [redacted], because you used a blacklisted term: ``{term}``, watch your language. If you think this is an error and/or the term should be whitelisted, please contact a member of staff.\nYour message for the sake of completion: ```{message.content}```")
                                except discord.Forbidden:
                                    await delivery_channel.send(f"I also tried DMing the person this, but he either has me blocked, or doesn't allow DM's")
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
