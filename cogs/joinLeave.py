import asyncio

import discord
from discord import Colour
from discord.ext import commands
from utils import logger
import utils.globals as GG

log = logger.logger

TRACKER = 737222675293929584


class JoinLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        tracker = await self.bot.fetch_channel(TRACKER)
        bots = sum(1 for m in guild.members if m.bot)
        members = len(guild.members)
        ratio = bots / members
        embed = discord.Embed(color=Colour.green())
        embed.title = f"Joined Server"
        embed.description = f"{guild}"
        embed.add_field(name="Members", value=f"{members - bots}")
        embed.add_field(name="Bots", value=f"{bots}")
        embed.add_field(name="** **", value="** **")
        embed.add_field(name="Owner", value=f"{guild.owner}")
        embed.add_field(name="Mention", value=f"{guild.owner.mention}")
        embed.add_field(name="Id", value=f"{guild.owner.id}")
        embed.set_footer(text=f"{guild.id}")
        await tracker.send(embed=embed)
        if ratio >= 0.6 and members >= 20:
            log.info("Detected bot collection server ({}), ratio {}. Leaving.".format(guild.id, ratio))
            try:
                await guild.owner.send("Please do not add me to bot collection servers. "
                                       "Your server was flagged for having over 60% bots. "
                                       "If you believe this is an error, please PM the bot author.")
            except:
                pass
            await asyncio.sleep(members / 200)
            await guild.leave()
        else:
            await self.bot.change_presence(
                activity=discord.Game(f"with {len(self.bot.guilds)} servers | !help | v{self.bot.version}"),
                afk=True)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        tracker = await self.bot.fetch_channel(TRACKER)
        bots = sum(1 for m in guild.members if m.bot)
        members = len(guild.members)
        embed = discord.Embed(color=Colour.red())
        embed.title = f"Left Server"
        embed.description = f"{guild}"
        embed.add_field(name="Members", value=f"{members - bots}")
        embed.add_field(name="Bots", value=f"{bots}")
        embed.add_field(name="** **", value="** **")
        embed.add_field(name="Owner", value=f"{guild.owner}")
        embed.add_field(name="Mention", value=f"{guild.owner.mention}")
        embed.add_field(name="Id", value=f"{guild.owner.id}")
        embed.set_footer(text=f"{guild.id}")
        await tracker.send(embed=embed)
        await self.bot.change_presence(
            activity=discord.Game(f"with {len(self.bot.guilds)} servers | !help | v{self.bot.version}"),
            afk=True)
        await GG.DB.srd_enabled.delete_one({"guildId": guild.id})


def setup(bot):
    log.info("[Event] Join and Leave Logging...")
    bot.add_cog(JoinLeave(bot))
