import typing
import discord
from discord.ext import commands
from utils import logger

log = logger.logger


class Release(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def release(self, ctx):
        pass


def setup(bot):
    log.info("Loading Releases Cog...")
    bot.add_cog(Release(bot))
