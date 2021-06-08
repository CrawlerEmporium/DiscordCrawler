import discord
from discord.ext import commands

import utils.globals as GG
from utils import logger
from utils.checks import is_staff_trouble
from utils.functions import try_delete

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
    @is_staff_trouble()
    async def nudge(self, ctx, messages: commands.Greedy[int]):
        msgs = []
        msgAuthors = []
        channel = self.bot.get_channel(ctx.message.channel.id)
        perms = ctx.guild.me.permissions_in(ctx.channel)

        if ctx.author.roles is not None:
            for r in ctx.author.roles:
                if r.id not in GG.STAFF and r.id == 593720945324326914:
                    if ctx.message.channel.id not in [470673352395325455, 607182631381237771, 586998165962490023, 470680051638075423]:
                        await try_delete(ctx.message)
                        await ctx.send("You are only allowed to nudge messages to the issue channels.")
                        return

        for message in messages:
            try:
                msg = await ctx.channel.fetch_message(message)
                if msg.author not in msgAuthors:
                    msgAuthors.append(msg.author)
                msgs.append(msg)
                await msg.delete()
            except:
                for channel in ctx.guild.text_channels:
                    perms = ctx.guild.me.permissions_in(channel)
                    if channel == ctx.channel or not perms.read_messages or not perms.read_message_history:
                        continue
                    try:
                        msg = await channel.fetch_message(message)
                        if msg.author not in msgAuthors:
                            msgAuthors.append(msg.author)
                        msgs.append(msg)
                        await msg.delete()
                    except:
                        continue
                    else:
                        break

        await try_delete(ctx.message)

        length = len(messages)
        if length <= 0:
            await ctx.send("I need one or more message Ids")
        else:
            authors = ""
            for author in msgAuthors:
                authors += f"{author.mention}, "
            message = f"{authors[:-2]} Your recent {singleOrMulti(length)[0]} should have been posted in this channel. (see the channel description below).\n" \
                      f"Your prior {singleOrMulti(length)[0]} {singleOrMulti(length)[1]} removed and {singleOrMulti(length)[2]} appended below. Thank you for helping keep conversations in their intended topics.\n\n" \
                      f"Channel Description: {ctx.message.channel.topic}"
            if perms.manage_webhooks:
                webhook = await ctx.channel.create_webhook(name="Nudging")
                await ctx.send(content=message)
                for msg in msgs:
                    await webhook.send(content=msg.content.replace('@everyone', '@еveryone').replace('@here', '@hеre'),
                                       username=msg.author.display_name, avatar_url=msg.author.avatar_url)
                await webhook.delete()
            else:
                embed = discord.Embed()
                embed.add_field(name="Channel Description", value=ctx.message.channel.topic, inline=False)
                embed.add_field(name="Your original posts", value=msgs[0].content, inline=False)
                for msg in msgs[1:]:
                    embed.add_field(name="** **", value=msg.content, inline=False)
                await ctx.send(content=message, embed=embed)


def setup(bot):
    log.info("[Cog] Nudge")
    bot.add_cog(Nudge(bot))
