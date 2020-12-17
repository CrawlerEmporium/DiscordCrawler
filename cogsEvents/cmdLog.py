from discord.ext import commands

from utils import logger

log = logger.logger


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        try:
            log.info(
                "cmd: chan {0.message.channel} ({0.message.channel.id}), serv {0.message.guild} ({0.message.guild.id}), "
                "auth {0.message.author} ({0.message.author.id}): {0.message.content}".format(
                    ctx))
        except AttributeError:
            log.info("Command in PM with {0.message.author} ({0.message.author.id}): {0.message.content}".format(ctx))


def setup(bot):
    log.info("[Event] Command Logging...")
    bot.add_cog(Logging(bot))
