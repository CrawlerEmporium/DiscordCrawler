import discord
from discord.ext import commands

from utils import globals as GG
from utils.checks import is_staff_trouble
from crawler_utilities.utils.functions import try_delete

log = GG.log


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
    @commands.guild_only()
    async def nudge(self, ctx, messages: commands.Greedy[int]):
        msgs = []
        msgAuthors = []

        if ctx.author.roles is not None:
            for r in ctx.author.roles:
                if r.id not in GG.STAFF and r.id == 593720945324326914:
                    if ctx.message.channel.id not in [1007247958435168316, 470680051638075423]:
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
                channelList = ctx.guild.text_channels + ctx.guild.threads
                for channel in channelList:
                    perms = channel.permissions_for(ctx.guild.me)
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
            await ctx.channel.send("I need one or more message Ids")
        else:
            authors = ""
            for author in msgAuthors:
                authors += f"{author.mention}, "
            if ctx.channel.permissions_for(ctx.guild.me).manage_webhooks:
                if isinstance(ctx.channel, discord.threads.Thread):
                    message = f"{authors[:-2]} Your recent {singleOrMulti(length)[0]} should have been posted in this thread.\n" \
                              f"Your prior {singleOrMulti(length)[0]} {singleOrMulti(length)[1]} removed and {singleOrMulti(length)[2]} appended below. Thank you for helping keep conversations in their intended topics.\n\n"
                    webhook = await ctx.channel.parent.create_webhook(name="Nudging")
                    await ctx.channel.send(content=message)
                    for msg in msgs:
                        await webhook.send(content=msg.content.replace('@everyone', '@еveryone').replace('@here', '@hеre'),
                                           username=msg.author.display_name, avatar_url=msg.author.display_avatar.url, thread=ctx.channel)
                    await webhook.delete()
                else:
                    message = f"{authors[:-2]} Your recent {singleOrMulti(length)[0]} should have been posted in this channel. (see the channel description below).\n" \
                              f"Your prior {singleOrMulti(length)[0]} {singleOrMulti(length)[1]} removed and {singleOrMulti(length)[2]} appended below. Thank you for helping keep conversations in their intended topics.\n\n" \
                              f"Channel Description: {ctx.message.channel.topic}"
                    webhook = await ctx.channel.create_webhook(name="Nudging")
                    await ctx.channel.send(content=message)
                    for msg in msgs:
                        await webhook.send(content=msg.content.replace('@everyone', '@еveryone').replace('@here', '@hеre'),
                                           username=msg.author.display_name, avatar_url=msg.author.display_avatar.url)
                    await webhook.delete()
            else:
                embed = discord.Embed()
                if not isinstance(ctx.channel, discord.threads.Thread):
                    embed.add_field(name="Channel Description", value=ctx.message.channel.topic, inline=False)
                embed.add_field(name="Your original posts", value=msgs[0].content, inline=False)
                for msg in msgs[1:]:
                    embed.add_field(name="** **", value=msg.content, inline=False)
                await ctx.send(content=message, embed=embed)


def setup(bot):
    log.info("[Cog] Nudge")
    bot.add_cog(Nudge(bot))
