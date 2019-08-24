import asyncio
import discord
import utils.globals as GG

from discord.ext import commands
from utils import logger
from DBService import DBService

log = logger.logger

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prune'])
    @GG.is_staff()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, *limit):
        if GG.checkPermission(ctx, "mm"):
            try:
                limit = int(limit[0])
            except IndexError:
                limit = 1
            deleted = 0
            while limit >= 1:
                cap = min(limit, 100)
                deleted += len(await ctx.channel.purge(limit=cap, before=ctx.message))
                limit -= cap
            tmp = await ctx.send(f'**:put_litter_in_its_place:** {deleted} Messages deleted')
            await asyncio.sleep(15)
            await tmp.delete()
            await ctx.message.delete()
        else:
            ctx.send("I don't have the Manage_Messages permission. It's a mandatory permission, I have noted my owner about this. Please give me this permission, I will end up leaving the server if it happens again.")
        await GG.upCommand("purge")


def setup(bot):
    log.info("Loading Purge Cog...")
    bot.add_cog(Purge(bot))
