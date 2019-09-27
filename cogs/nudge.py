import asyncio
import discord
import utils.globals as GG

from discord.ext import commands
from utils import logger
from DBService import DBService

log = logger.logger


class Nudge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nudge(self, ctx, messageId):
        channel = self.bot.get_channel(ctx.message.channel.id)
        try:
            msg = await ctx.channel.fetch_message(messageId)
        except:
            for channel in ctx.guild.text_channels:
                perms = ctx.guild.me.permissions_in(channel)
                if channel == ctx.channel or not perms.read_messages or not perms.read_message_history:
                    continue
                try:
                    msg = await channel.fetch_message(messageId)
                except:
                    continue
                else:
                    break

        message = f"{msg.author.mention} Your recent post should have been posted in this channel (see <#472697130692116500> and the channel description below).\n" \
            f"Your prior post was removed and is appended below. Thank you for helping keep conversations in their intended topics."

        embed = discord.Embed()
        embed.add_field(name="Channel Description",value=ctx.message.channel.topic)
        embed.add_field(name="Your original post",value=msg.content)

        await msg.delete()
        await ctx.message.delete()

        await ctx.send(content=message, embed=embed)




def setup(bot):
    log.info("Loading Nudge Cog...")
    bot.add_cog(Nudge(bot))
