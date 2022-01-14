import asyncio
from datetime import datetime, timedelta

import discord
from discord import Thread, slash_command, permissions, Option
from discord.enums import SlashCommandOptionType
from discord.ext import commands, tasks
from crawler_utilities.handlers import logger

import utils.globals as GG
from crawler_utilities.utils.confirmation import BotConfirmation
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
        channel = await guild.fetch_channel(int(thread['threadId']))
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

    @slash_command(name="keepthreadalive", guild_ids=[584842413135101990])
    async def kta(self, ctx, channel: Option(SlashCommandOptionType.channel, "Which thread do you want to keep alive?")):
        """[STAFF] Adds a watcher on a thread, so that it won't automatically archive after its time"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        await ctx.defer(ephemeral=True)
        if isinstance(channel, Thread):
            thread = await GG.MDB['threads'].find_one({"threadId": channel.id})
            if thread is not None:
                confirmation = BotConfirmation(ctx, 0x012345)
                await confirmation.confirm(f"K.T.A. (Keep Thread Active) is currently enabled for ``{channel.name}``.\nWould you like to disable it?", channel=ctx.channel)
                if confirmation.confirmed:
                    await confirmation.update(f"Confirmed, disabling K.T.A. ...", color=0x55ff55)
                    await GG.MDB['threads'].delete_one({"threadId": channel.id})
                    await asyncio.sleep(5)
                    await confirmation.quit()
                    return await ctx.respond(f"Thank you for using the K.T.A. (Keep Thread Active) feature.\nThis feature is now disabled for the thread ``{channel.name}``.")
                else:
                    await confirmation.quit()

            if channel.auto_archive_duration == 60:
                return await ctx.respond("The K.T.A. (Keep Thread Active) feature can only be enabled in threads that have an auto archiving duration of 1 day or higher.")

            confirmation = BotConfirmation(ctx, 0x012345)
            await confirmation.confirm(f"K.T.A. (Keep Thread Active) is currently not enabled for ``{channel.name}``.\nWould you like to enable it?", channel=ctx.channel)
            if confirmation.confirmed:
                await confirmation.update(f"Confirmed, enabling K.T.A. ...", color=0x55ff55)
                type = None
                if channel.auto_archive_duration == 1440:
                    type = 2
                if channel.auto_archive_duration == 4320:
                    type = 3
                if channel.auto_archive_duration == 10080:
                    type = 4

                thread = {
                    "threadId": channel.id,
                    "guildId": ctx.guild.id,
                    "type": type
                }
                await GG.MDB['threads'].insert_one(thread)
                await asyncio.sleep(5)
                await confirmation.quit()
                return await ctx.respond(f"Thank you for using the K.T.A. (Keep Threads Active) feature.\n"
                                   f"The thread ``{channel.name}`` will now be watched and prevented from being automatically archived.\n\n"
                                   f"You can disable this by running the same command again.")
            else:
                await confirmation.quit()
        else:
            return await ctx.respond(f"{ctx.channel.name} is not a thread, you can only enable the K.T.A. (Keep Threads Active) feature on threads.", ephemeral=True)


def setup(bot):
    log.info("[Cog] KeepThreadsActive")
    bot.add_cog(KeepThreadsActive(bot))
