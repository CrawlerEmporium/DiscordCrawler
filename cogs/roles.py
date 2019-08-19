import discord
import utils.globals as GG

from discord.ext import commands
from utils import logger
from DBService import DBService

log = logger.logger

def getGuild(self, payload):
    guild = self.bot.get_guild(payload.guild_id)
    return guild

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addRole(self, ctx, channelId, messageId, roleId, emoji):
        channel = await self.bot.fetch_channel(channelId)
        message = await channel.fetch_message(messageId)
        try:
            await message.add_reaction(emoji)
        except:
            await ctx.send("Unknown Emoji, please only use default emoji's or emoji's from this server.")
        else:
            DBService.exec(
                "INSERT INTO ReactionRoles (GuildId, MessageId, RoleId, Emoji) VALUES (" + str(
                    ctx.guild.id) + "," + str(messageId) + "," + str(roleId) + ",'" + str(emoji) + "')")
            GG.reloadReactionRoles()



    @commands.command()
    async def removeRole(self, ctx):
        return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = payload.emoji

        if payload.message_id in GG.REACTIONROLES:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emoji = payload.emoji
        return

def setup(bot):
    log.info("Loading Roles Cog...")
    bot.add_cog(Roles(bot))
