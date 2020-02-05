import discord
from discord.ext import commands

import utils.globals as GG
from utils import logger

log = logger.logger


def singleOrMulti(length):
    if length >= 2:
        return ["posts", "were", "are"]
    else:
        return ["post", "was", "is"]


class Nudge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @GG.is_staff()
    async def nudge(self, ctx, messages: commands.Greedy[discord.Message]):
        length = len(messages)
        if length <= 0:
            await ctx.send("I need one or more message Ids")
        else:
            channel = self.bot.get_channel(messages[0].channel.id)
            msgs = []
            for message in messages:
                try:
                    msg = await ctx.channel.fetch_message(message.id)
                    msgs.append(msg)
                    await msg.delete()
                except:
                    for channel in ctx.guild.text_channels:
                        perms = ctx.guild.me.permissions_in(channel)
                        if channel == ctx.channel or not perms.read_messages or not perms.read_message_history:
                            continue
                        try:
                            msg = await channel.fetch_message(message.id)
                            msgs.append(msg)
                            await msg.delete()
                        except:
                            continue
                        else:
                            break

            message = f"{messages[0].author.mention} Your recent {singleOrMulti(length)[0]} should have been posted in this channel (see the channel description below).\n" \
                      f"Your prior {singleOrMulti(length)[0]} {singleOrMulti(length)[1]} removed and {singleOrMulti(length)[2]} appended below. Thank you for helping keep conversations in their intended topics."

            embed = discord.Embed()
            embed.add_field(name="Channel Description", value=ctx.message.channel.topic, inline=False)
            embed.add_field(name="Your original posts", value=msgs[0].content, inline=False)
            for msg in msgs[1:]:
                embed.add_field(name="** **", value=msg.content, inline=False)

            await ctx.message.delete()
            await ctx.send(content=message, embed=embed)


def setup(bot):
    log.info("Loading Nudge Cog...")
    bot.add_cog(Nudge(bot))
