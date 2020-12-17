import traceback

import asyncio
from aiohttp import ClientResponseError, ClientOSError
from discord import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands import CommandInvokeError
from utils.errors import CrawlerException, InvalidArgument, EvaluationError
import utils.globals as GG
from utils import logger
from utils.functions import gen_error_message, discord_trim

log = logger.logger


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        owner = self.bot.get_user(GG.OWNER)
        if isinstance(error, commands.CommandNotFound):
            return
        log.debug("Error caused by message: `{}`".format(ctx.message.content))
        log.debug('\n'.join(traceback.format_exception(type(error), error, error.__traceback__)))
        if isinstance(error, CrawlerException):
            return await ctx.send(str(error))
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error,
                      (commands.MissingRequiredArgument, commands.BadArgument, commands.NoPrivateMessage, ValueError)):
            return await ctx.send("Error: " + str(
                error) + f"\nUse `{ctx.prefix}oldhelp " + ctx.command.qualified_name + "` for help.")
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send("Error: You are not allowed to run this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send("This command is on cooldown for {:.1f} seconds.".format(error.retry_after))
        elif isinstance(error, CommandInvokeError):
            original = error.original
            if isinstance(original, EvaluationError):  # PM an alias author tiny traceback
                e = original.original
                if not isinstance(e, CrawlerException):
                    tb = f"```py\nError when parsing expression {original.expression}:\n" \
                         f"{''.join(traceback.format_exception(type(e), e, e.__traceback__, limit=0, chain=False))}\n```"
                    try:
                        await ctx.author.send(tb)
                    except Exception as e:
                        log.info(f"Error sending traceback: {e}")
            if isinstance(original, CrawlerException):
                return await ctx.send(str(original))
            if isinstance(original, Forbidden):
                try:
                    return await ctx.author.send(
                        f"Error: I am missing permissions to run this command. "
                        f"Please make sure I have permission to send messages to <#{ctx.channel.id}>."
                    )
                except:
                    try:
                        return await ctx.send(f"Error: I cannot send messages to this user.")
                    except:
                        return
            if isinstance(original, NotFound):
                return await ctx.send("Error: I tried to edit or delete a message that no longer exists.")
            if isinstance(original, ValueError) and str(original) in ("No closing quotation", "No escaped character"):
                return await ctx.send("Error: No closing quotation.")
            if isinstance(original, (ClientResponseError, InvalidArgument, asyncio.TimeoutError, ClientOSError)):
                return await ctx.send("Error in Discord API. Please try again.")
            if isinstance(original, HTTPException):
                if original.response.status == 400:
                    return await ctx.send("Error: Message is too long, malformed, or empty.")
                if original.response.status == 500:
                    return await ctx.send("Error: Internal server error on Discord's end. Please try again.")
            if isinstance(original, OverflowError):
                return await ctx.send(f"Error: A number is too large for me to store.")

        error_msg = gen_error_message()

        await ctx.send(
            f"Error: {str(error)}\nUh oh, that wasn't supposed to happen! "
            f"Please join the Support Discord ($support) and tell the developer that: **{error_msg}!**")
        try:
            await owner.send(
                f"**{error_msg}**\n" \
                + "Error in channel {} ({}), server {} ({}): {}\nCaused by message: `{}`".format(
                    ctx.channel, ctx.channel.id, ctx.guild,
                    ctx.guild.id, repr(error),
                    ctx.message.content))
        except AttributeError:
            await owner.send(f"**{error_msg}**\n" \
                             + "Error in PM with {} ({}), shard 0: {}\nCaused by message: `{}`".format(
                ctx.author.mention, str(ctx.author), repr(error), ctx.message.content))
        for o in discord_trim(tb):
            await owner.send(o)
        log.error("Error caused by message: `{}`".format(ctx.message.content))


def setup(bot):
    log.info("[Event] Errors...")
    bot.add_cog(Errors(bot))
