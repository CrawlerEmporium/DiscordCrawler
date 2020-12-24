import discord

import utils.globals as GG

from discord.ext import commands
from utils import logger

log = logger.logger


def getGuild(self, payload):
    guild = self.bot.get_guild(payload.guild_id)
    return guild


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def addRole(self, ctx, channelId, messageId, roleId, emoji):
        channel = await self.bot.fetch_channel(channelId)
        message = await channel.fetch_message(messageId)
        try:
            await message.add_reaction(emoji)
        except:
            await ctx.send("Unknown Emoji, please only use default emoji's or emoji's from this server.")
        else:
            try:
                await GG.MDB['reactionroles'].insert_one({"guildId": ctx.guild.id, "messageId": messageId, "roleId": roleId, "emoji": str(emoji)})
                GG.REACTIONROLES = await GG.reloadReactionRoles()
            except:
                await message.remove_reaction(emoji, ctx.guild.me)
                await ctx.send(
                    "You are trying to add a reaction to the message that already exists, or the role it would give as reaction is already in use.\nPlease check if this is correct, if not, please contact my owner in `$support`")

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def removeRole(self, ctx, channelId, messageId, roleId, emoji: discord.Emoji):
        channel = await self.bot.fetch_channel(channelId)
        message = await channel.fetch_message(messageId)
        try:
            reactions = message.reactions
            for x in reactions:
                if x.emoji == emoji:
                    users = await x.users().flatten()
                    for y in users:
                        await message.remove_reaction(emoji, y)
        except:
            await ctx.send(
                "Unknown Emoji, please check if this emoji is still present as a reaction on the message you supplied.")
        else:
            await GG.MDB['reactionroles'].delete_one({"guildId": ctx.guild.id, "messageId": messageId, "roleId": roleId, "emoji": str(emoji)})
            GG.REACTIONROLES = await GG.reloadReactionRoles()

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def removeAll(self, ctx, roleId):
        guild = await self.bot.fetch_guild(ctx.guild.id)
        Role = guild.get_role(roleId)
        if Role is not None:
            members = guild.members
            await ctx.send(f"Removing {Role.name} from {len(members)} members.")
            async with ctx.channel.typing():
                for x in members:
                    Member = await guild.fetch_member(x.id)
                    await Member.remove_roles(Role)
            await ctx.send(f"Removed {Role.name} from {len(members)} members.")
        else:
            await ctx.send(f"Role doesn't exist, or you used a wrong id.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id in GG.REACTIONROLES:
            emoji = payload.emoji
            server = GG.REACTIONROLES[payload.message_id]
            roleId = None
            for x in server:
                dbEmoji = x[1][2:].split(":")
                if emoji.name == dbEmoji[0] or emoji.name == x[1]:
                    roleId = int(x[0])
                    userId = payload.user_id
                    guildId = payload.guild_id
                    guild = await self.bot.fetch_guild(guildId)
                    await guild.chunk()
                    Role = guild.get_role(roleId)
                    Member = await guild.fetch_member(userId)
                    await Member.add_roles(Role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id in GG.REACTIONROLES:
            emoji = payload.emoji
            server = GG.REACTIONROLES[payload.message_id]
            roleId = None
            for x in server:
                dbEmoji = x[1][2:].split(":")
                if emoji.name == dbEmoji[0] or emoji.name == x[1]:
                    roleId = int(x[0])
                    userId = payload.user_id
                    guildId = payload.guild_id
                    guild = await self.bot.fetch_guild(guildId)
                    await guild.chunk()
                    Role = guild.get_role(roleId)
                    Member = await guild.fetch_member(userId)
                    await Member.remove_roles(Role)


def setup(bot):
    log.info("[Cog] Roles")
    bot.add_cog(Roles(bot))
