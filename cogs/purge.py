import asyncio
import discord
import utils.globals as GG

from discord.ext import commands
from utils import logger
from DBService import DBService

log = logger.logger

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['prune'])
    @GG.is_staff()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, limit):
        if GG.checkPermission(ctx, "mm"):
            try:
                if isinstance(int(limit), int):

                    message = await ctx.send(f"Are you sure you want to remove {limit} messages?")
                    await message.add_reaction('❌')

                    await self.waitChangeMessage(ctx, message, limit)

                else:
                    msg = await ctx.send("I need a number for how many messages I need to purge...")
                    await asyncio.sleep(4)
                    await msg.delete()
            except ValueError:
                msg = await ctx.send("I need a number for how many messages I need to purge...")
                await asyncio.sleep(4)
                await msg.delete()
        else:
            await ctx.send("I don't have the Manage_Messages permission. It's a mandatory permission, I have noted my owner about this. Please give me this permission, I will end up leaving the server if it happens again.")
        await GG.upCommand("purge")


    async def waitChangeMessage(self, ctx, message, limit):
        def check(reaction, user):
            return (user == ctx.message.author and str(reaction.emoji) == '❌')

        try:
            await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            if not isinstance(message.channel, discord.DMChannel):
                await message.clear_reactions()
        else:
            await message.delete()
            try:
                limit = int(limit)
            except IndexError:
                limit = 1
            deleted = 0
            while limit >= 1:
                cap = min(limit, 100)
                deleted += len(await ctx.channel.purge(limit=cap, before=ctx.message))
                limit -= cap
            tmp = await ctx.send(f'**:put_litter_in_its_place:** {deleted} Messages deleted')
            await asyncio.sleep(8)
            await tmp.delete()
            await ctx.message.delete()

def setup(bot):
    log.info("Loading Purge Cog...")
    bot.add_cog(Purge(bot))
