import discord
import utils.globals as GG

from discord.ext import commands
from utils import logger
from DBService import DBService

log = logger.logger

categories = [
    'ANON',
    'DELIVERY',
    'ANNOUNCEMENT']

def list_embed(list_personals, author):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description='\n'.join(['• `' + i[1] + '`' for i in list_personals]), color=author.color)
    else:
        embed = discord.Embed(description='\n'.join(['• `' + i[1] + '`' for i in list_personals]))
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
            DBService.exec(
                "INSERT INTO ServerStaff (Guild, Roles) VALUES (" + str(ctx.guild.id) + "," + str(role.id) + ")")
            GG.STAFF.append(int(role.id))
            await ctx.send(f"{role.name} was added to the staff list.")
        await GG.upCommand("addstaff")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def stafflist(self, ctx):
        """[STAFF ONLY]"""
        user_quotes = DBService.exec(
            "SELECT * FROM ServerStaff WHERE Guild = " + str(ctx.message.guild.id)).fetchall()
        await ctx.send(embed=list_embed(user_quotes, ctx.author))
        await GG.upCommand("stafflist")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def delstaff(self, ctx, role: discord.Role):
        """[STAFF ONLY]"""
        if role.id in GG.STAFF:
            DBService.exec("DELETE FROM ServerStaff WHERE Roles = " + str(role.id) + "")
            GG.STAFF.remove(int(role.id))
            await ctx.send(f"{role.name} was removed from the staff list.")
        else:
            try:
                DBService.exec("DELETE FROM ServerStaff WHERE Roles = " + str(role.id) + "")
            except Exception as e:
                log.error("Tried to deleting a staff role that doesn't exist in the database.")
            await ctx.send(f"{role.name} is not on the staff list.")
        await GG.upCommand("delstaff")

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    @commands.guild_only()
    async def prefix(self, ctx, prefix: str = None):
        """Sets the bot's prefix for this server.
        Forgot the prefix? Reset it with "@5eCrawler#2771 prefix !".
        """
        guild_id = str(ctx.guild.id)
        if prefix is None:
            return await ctx.send(f"My current prefix is: `{self.bot.get_server_prefix(ctx.message)}`")
        DBService.exec(
            "REPLACE INTO Prefixes (Guild, Prefix) VALUES (" + str(ctx.guild.id) + ",'" + str(prefix) + "')")
        self.bot.prefixes[guild_id] = prefix
        GG.PREFIXES[guild_id] = prefix
        await ctx.send("Prefix set to `{}` for this server.".format(prefix))
        await GG.upCommand("prefix")


    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def addchannel(self, ctx, TYPE: str, channel: discord.TextChannel):
        """[STAFF ONLY]"""
        if GG.checkPermission(ctx,"mm"):
            TYPE = TYPE.upper()
            if TYPE in categories:
                if channel.id in GG.CHANNEL:
                    await ctx.send(f"{channel.name} is already on the special channel list.")
                else:
                    DBService.exec(
                        "INSERT INTO ChannelInfo (Guild, Channel, Type) VALUES (" + str(ctx.guild.id) + "," + str(
                            channel.id) + ",'" + str(TYPE) + "')")
                    GG.CHANNEL[channel.id] = str(TYPE)
                    await ctx.send(f"{channel.name} was added to the special channel list as {TYPE}")
            else:
                await ctx.send(
                    f"{TYPE} is not part of the list of specialized channels you can make. Please use one of the following:\n{categories}")
        else:
            ctx.send(
                "I don't have the Manage_Messages permission. It's a mandatory permission, I have noted my owner about this. Please give me this permission, I will end up leaving the server if it happens again.")
        await GG.upCommand("addchannel")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def delchannel(self, ctx, channel: discord.TextChannel):
        """[STAFF ONLY]"""
        if channel.id in GG.CHANNEL:
            DBService.exec("DELETE FROM ChannelInfo WHERE Channel = " + str(channel.id) + "")
            del GG.CHANNEL[channel.id]
            await ctx.send(f"{channel.name} was removed from the special channel list.")
        else:
            try:
                DBService.exec("DELETE FROM ChannelInfo WHERE Channel = " + str(channel.id) + "")
            except Exception as e:
                log.error("Tried to deleting a channel that doesn't exist in the database.")
            await ctx.send(f"{channel.name} is not on the special channel list.")
        await GG.upCommand("delchannel")

    @commands.command()
    @GG.is_staff()
    @commands.guild_only()
    async def channeltypes(self, ctx):
        """[STAFF ONLY]"""
        await ctx.send(f"You can use one of the following channel types:\n{categories}")
        await GG.upCommand("channeltypes")


def setup(bot):
    log.info("Loading ServerCommands Cog...")
    bot.add_cog(ServerCommands(bot))
