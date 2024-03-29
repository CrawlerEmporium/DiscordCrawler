import asyncio

import discord
from discord import slash_command, Option

from discord.ext import commands
from utils import globals as GG
from crawler_utilities.utils.confirmation import BotConfirmation

log = GG.log


def pinned(message: discord.Message):
    if message.pinned:
        return False
    else:
        return True


class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="purge")
    @commands.guild_only()
    async def purge(self, ctx, limit: Option(int, "How many messages do you want to delete?")):
        """[STAFF] Purges messages from a channel, skips pinned messages"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        await ctx.defer(ephemeral=True)
        confirmation = BotConfirmation(ctx, 0x012345)
        channel = await self.bot.fetch_channel(ctx.interaction.channel_id)
        await confirmation.confirm(f"Are you sure you want to remove {limit} messages?", channel=channel)
        if confirmation.confirmed:
            await confirmation.update(f"Confirmed, **:put_litter_in_its_place:** deleting {limit} messages...", color=0x55ff55)
            messages = await channel.history(limit=1).flatten()
            try:
                limit = int(limit)
            except IndexError:
                limit = 1
            deleted = 0
            while limit >= 1:
                cap = min(limit, 100)
                deleted += len(await channel.purge(check=pinned, limit=cap, before=messages[0]))
                limit -= cap
            await asyncio.sleep(8)
            await confirmation.quit()
            await ctx.respond(f"Succesfully purged {deleted} messages", ephemeral=True)
        else:
            await confirmation.quit()
            await ctx.respond("Purge canceled", ephemeral=True)


def setup(bot):
    log.info("[Cog] Purge")
    bot.add_cog(Purge(bot))
