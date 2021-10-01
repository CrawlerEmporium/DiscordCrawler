from datetime import datetime, timedelta

from discord import Thread
from discord.ext import commands, tasks
from crawler_utilities.handlers import logger

import utils.globals as GG
from crawler_utilities.utils.functions import try_delete

log = logger.logger


class KeepThreadsActive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threadActivator.start()

    @tasks.loop(hours=1)
    async def threadActivator(self):
        threads = await GG.MDB['threads'].find({}).to_list(length=None)
        for thread in threads:
            await self.checkLastMessage(thread)

    async def checkLastMessage(self, thread):
        guild = await self.bot.fetch_guild(int(thread['guildId']))
        channel = await guild.fetch_channel(int(thread['channelId']))
        time = datetime.utcnow()
        if int(thread['type']) == 2:  # 1 day
            time -= timedelta(hours=23)
        if int(thread['type']) == 3:  # 3 days
            time -= timedelta(hours=71)
        if int(thread['type']) == 4:  # 7 days
            time -= timedelta(hours=167)
        messages = await channel.history(after=time).flatten()
        if len(messages) == 0:
            await channel.send("This thread was scheduled to be automatically archived for inactivity.\n"
                               "But a member of staff enabled the K.T.A. (Keep Threads Active) feature for this thread.\n\n"
                               "A member of staff can disable this by re-running the ``kta`` command.")

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def kta(self, ctx):
        await try_delete(ctx.message)
        if isinstance(ctx.channel, Thread):

            thread = await GG.MDB['threads'].find_one({"threadId": ctx.channel.id})
            if thread is not None:
                await GG.MDB['threads'].delete_one({"threadId": ctx.channel.id})
                return await ctx.send(f"Thank you for using the K.T.A. (Keep Thread Active) feature.\nThis feature is now disabled for this thread ``{ctx.channel.name}``.", delete_after=5)

            type = None
            if ctx.channel.auto_archive_duration == 60:
                return await ctx.send("The K.T.A. (Keep Thread Active) feature can only be enabled in threads that have an auto archiving duration of 1 day or higher.", delete_after=5)
            if ctx.channel.auto_archive_duration == 1440:
                type = 2
            if ctx.channel.auto_archive_duration == 4320:
                type = 3
            if ctx.channel.auto_archive_duration == 10080:
                type = 4

            thread = {
                "threadId": ctx.channel.id,
                "guildId": ctx.guild.id,
                "type": type
            }
            await GG.MDB['threads'].insert_one(thread)
            await ctx.send(f"Thank you for using the K.T.A. (Keep Threads Active) feature.\n"
                           f"This thread ``{ctx.channel.name}`` will now be watched and prevented from being automatically archived.\n\n"
                           f"You can disable this by running the same command again.")
        else:
            await ctx.send("This is not a thread, you can only enable the K.T.A. (Keep Threads Active) feature in threads.", delete_after=5)


def setup(bot):
    log.info("[Cog] KeepThreadsActive")
    bot.add_cog(KeepThreadsActive(bot))
