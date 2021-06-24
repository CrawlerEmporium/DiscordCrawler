import discord
import utils.globals as GG

from discord.ext import commands
from crawler_utilities.utils import logger

log = logger.logger

categories = ['ANON', 'DELIVERY', 'MODDECISION', 'BLACKLIST']


def getRole(roleID, ctx):
    guild = ctx.message.guild
    role = guild.get_role(roleID)
    return role.name


def list_embed(list_personals, author, ctx):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():

        embed = discord.Embed(description='\n'.join(['• `' + getRole(i['roles'], ctx) + '`' for i in list_personals]), color=author.color)
    else:
        embed = discord.Embed(description='\n'.join(['• `' + getRole(i['roles'], ctx) + '`' for i in list_personals]))
    embed.title = "Roles that are considered staff according to the bot."
    return embed


class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def addstaff(self, ctx, role: discord.Role):
        """[STAFF ONLY]"""
        if role.id in GG.STAFF:
            await ctx.send(f"{role.name} is already on the staff list.")
        else:
            await GG.MDB['serverstaff'].insert_one({"guild": ctx.guild.id, "roles": int(role.id)})
            GG.STAFF.append(int(role.id))
            await ctx.send(f"{role.name} was added to the staff list.")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def stafflist(self, ctx):
        """[STAFF ONLY]"""
        user_quotes = await GG.MDB['serverstaff'].find({"guild": ctx.message.guild.id}).to_list(length=None)
        if user_quotes is not None:
            await ctx.send(embed=list_embed(user_quotes, ctx.author, ctx))
        else:
            await ctx.send("This server has no roles assigned as staff.")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def delstaff(self, ctx, role: discord.Role):
        """[STAFF ONLY]"""
        exist = await GG.MDB['serverstaff'].find_one({"guild": ctx.guild.id, "roles": int(role.id)})
        if exist is not None:
            await GG.MDB['serverstaff'].delete_one({"guild": ctx.guild.id, "roles": int(role.id)})
            GG.STAFF.remove(int(role.id))
            await ctx.send(f"{role.name} was removed from the staff list.")
        else:
            await ctx.send(f"{role.name} is not on the staff list.")

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    @commands.guild_only()
    async def prefix(self, ctx, prefix: str = None):
        """Sets the bot's prefix for this server.
        Forgot the prefix? Reset it with "@DiscordCrawler#6716 prefix !".
        """
        guild_id = str(ctx.guild.id)
        if prefix is None:
            return await ctx.send(f"My current prefix is: `{self.bot.get_server_prefix(ctx.message)}`")
        await GG.MDB['prefixes'].update_one({"guild": guild_id}, {"$set": {"prefix": str(prefix)}}, upsert=True)
        self.bot.prefixes[guild_id] = prefix
        GG.PREFIXES[guild_id] = prefix
        await ctx.send("Prefix set to `{}` for this server.".format(prefix))

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def addchannel(self, ctx, TYPE: str, channel: discord.TextChannel):
        """[STAFF ONLY]"""
        if GG.checkPermission(ctx, "mm"):
            TYPE = TYPE.upper()
            if TYPE in categories:
                channelExists = await GG.MDB['channelinfo'].find_one({"channel": channel.id})
                if channelExists is not None:
                    await ctx.send(f"{channel.name} is already on the special channel list.")
                else:
                    await GG.MDB['channelinfo'].insert_one({"guild": ctx.guild.id, "channel": channel.id, "type": TYPE})
                    GG.CHANNEL[channel.id] = str(TYPE)
                    await ctx.send(f"{channel.name} was added to the special channel list as {TYPE}")
            else:
                await ctx.send(
                    f"{TYPE} is not part of the list of specialized channels you can make. Please use one of the following:\n{categories}")
        else:
            await ctx.send(
                "I don't have the Manage_Messages permission. It's a mandatory permission, I have noted my owner about this. Please give me this permission, I will end up leaving the server if it happens again.")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def delchannel(self, ctx, channel: discord.TextChannel):
        """[STAFF ONLY]"""
        channelExists = await GG.MDB['channelinfo'].find_one({"channel": channel.id})
        if channelExists is not None:
            await GG.MDB['channelinfo'].delete_one({"channel": channel.id})
            del GG.CHANNEL[channel.id]
            await ctx.send(f"{channel.name} was removed from the special channel list.")
        else:
            await ctx.send(f"{channel.name} is not on the special channel list.")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def channeltypes(self, ctx):
        """[STAFF ONLY]"""
        await ctx.send(f"You can use one of the following channel types:\n{categories}")


def setup(bot):
    log.info("[Cog] ServerCommands")
    bot.add_cog(ServerCommands(bot))
