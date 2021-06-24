import discord

from discord.ext import commands
from crawler_utilities.utils.pagination import BotEmbedPaginator

from crawler_utilities.utils import logger
import utils.globals as GG
from crawler_utilities.utils.functions import try_delete

log = logger.logger


def list_embed(list_personals, author):
    embedList = []
    for i in range(0, len(list_personals), 10):
        lst = list_personals[i:i + 10]
        desc = ""
        for item in lst:
            desc += '• `' + str(item['name']) + '`\n'
        if isinstance(author, discord.Member) and author.color != discord.Colour.default():
            embed = discord.Embed(description=desc, color=author.color)
        else:
            embed = discord.Embed(description=desc)
        embed.set_author(name='Look commands', icon_url=author.avatar_url)
        embedList.append(embed)
    return embedList


class LookCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, hidden=True)
    async def look(self, ctx, trigger):
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await try_delete(ctx.message)
        trigger = trigger.lower()
        exist = await self.bot.mdb.look.find_one({"name": f"{trigger}"})
        if exist is not None:
            try:
                if ctx.message.author.dm_channel is not None:
                    DM = ctx.message.author.dm_channel
                else:
                    DM = await ctx.message.author.create_dm()

                await DM.send(exist['text'])
            except discord.Forbidden:
                pass

    @look.command(name='add', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def lookadd(self, ctx, trigger, *, text):
        trigger = trigger.lower()
        if trigger == "add" or trigger == "remove" or trigger == "list":
            await ctx.send("You can not use the words `add`, `remove` or `list` as they are commands themselves.")
            return
        exist = await self.bot.mdb.look.find_one({"name": f"{trigger}"})
        if exist is None:
            if not isinstance(ctx.message.channel, discord.DMChannel):
                await try_delete(ctx.message)
            await self.bot.mdb.look.insert_one({"name": f"{trigger}", 'text': f"{text}"})
            await ctx.send(f"A look with {trigger} was added.")
        else:
            if not isinstance(ctx.message.channel, discord.DMChannel):
                await try_delete(ctx.message)
            await ctx.send(f"A look for {trigger} already exists.")

    @look.command(name='remove', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def lookremove(self, ctx, trigger):
        trigger = trigger.lower()
        exist = await self.bot.mdb.look.find_one({"name": f"{trigger}"})
        if exist is not None:
            if not isinstance(ctx.message.channel, discord.DMChannel):
                await try_delete(ctx.message)
            await self.bot.mdb.look.delete_one({"name": f"{trigger}"})
            await ctx.send(f"A look with {trigger} was removed.")
        else:
            if not isinstance(ctx.message.channel, discord.DMChannel):
                await try_delete(ctx.message)
            await ctx.send(f"A look for {trigger} was not found.")

    @look.command(name='list', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def looklist(self, ctx):
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await try_delete(ctx.message)
        list = await self.bot.mdb.look.find({}).to_list(length=None)
        if len(list) > 0:
            embeds = list_embed(list, ctx.author)
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
        else:
            await ctx.send("No look commands found.")

def setup(bot):
    log.info("[Cog] Look")
    bot.add_cog(LookCommands(bot))
