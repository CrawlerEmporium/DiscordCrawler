import discord
from discord import Option, slash_command, Message

from discord.ext import commands
from cogsAdmin.models.honeypot import Honeypot as HoneypotModel
from cogsAdmin.utils import banHandler
from crawler_utilities.cogs.localization import get_command_kwargs
from utils import globals as GG

log = GG.log


class Honeypot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "honeypot"

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.isHoneypot(message)

    async def isHoneypot(self, message: discord.Message):
        if message.channel.id in GG.HONEYPOTCHANNELS:
            if message.author.id != GG.BOT:
                if not GG.is_staff_by_user_bool(message.author, message.channel.guild):
                    await banHandler.HoneypotCommand(self.bot, message.channel.guild, message.author, "You've been honeypotted. Most likely you were hacked or got scammed out of your account.")


    @slash_command(**get_command_kwargs(cogName, 'honeypot'))
    @commands.guild_only()
    async def HoneypotCmd(self, ctx, channel: Option(discord.TextChannel)):
        await ctx.defer()
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.HoneypotCommand(ctx, channel)

    async def HoneypotCommand(self, ctx, channel):
        if channel is None:
            return await ctx.send(
                "Channel wasn't found.\n\nCheck the ID, it might not be a channel.")

        honeypotChannel = await GG.MDB.honeypot.find_one({"guildId": ctx.interaction.guild_id, "channelId": channel.id})
        if honeypotChannel is None:
            honeypot = HoneypotModel(ctx.interaction.guild_id, channel.id)
        else:
            return await ctx.respond(f"{channel} was already set as honeypot channel. Posters will get banned from this moment on.")

        await GG.MDB.honeypot.insert_one(honeypot.to_dict())

        return await ctx.respond(f"{channel} set as honeypot channel. Posters will get banned from this moment on.")


def setup(bot):
    log.info("[Admin] Honeypot")
    bot.add_cog(Honeypot(bot))
