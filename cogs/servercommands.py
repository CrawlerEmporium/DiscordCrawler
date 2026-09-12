import discord
from discord import Option, slash_command
from urllib.parse import urlsplit

from discord.ext import commands
from utils import globals as GG

log = GG.log

categories = ['ANON', 'DELIVERY', 'MODDECISION', 'BLACKLIST']


def extract_appeal_path(appeal_url):
    appeal_url = appeal_url.strip()
    has_scheme = '://' in appeal_url
    url_value = appeal_url if has_scheme else f'https://{appeal_url}'

    try:
        parsed = urlsplit(url_value)
    except ValueError:
        return None

    if has_scheme or parsed.hostname in {'appeal.gg', 'www.appeal.gg'}:
        if parsed.hostname not in {'appeal.gg', 'www.appeal.gg'}:
            return None
        return parsed.path.strip('/')

    return appeal_url.strip('/')


def getRole(roleID, ctx):
    guild = ctx.guild
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

    @slash_command(name="addstaff")
    @commands.guild_only()
    async def addstaff(self, ctx, role: discord.Role):
        """[STAFF] Adds a role to the staff list"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        if role.id in GG.STAFF:
            return await ctx.respond(f"{role.name} is already on the staff list.", ephemeral=True)
        else:
            await GG.MDB['serverstaff'].insert_one({"guild": ctx.guild.id, "roles": int(role.id)})
            GG.STAFF.append(int(role.id))
            return await ctx.respond(f"{role.name} was added to the staff list.", ephemeral=True)

    @slash_command(name="stafflist")
    @commands.guild_only()
    async def stafflist(self, ctx):
        """[STAFF] Returns a list of all staff roles"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        user_quotes = await GG.MDB['serverstaff'].find({"guild": ctx.guild.id}).to_list(length=None)
        if user_quotes is not None:
            return await ctx.respond(embed=list_embed(user_quotes, ctx.author, ctx), ephemeral=True)
        else:
            return await ctx.respond("This server has no roles assigned as staff.", ephemeral=True)

    @slash_command(name="delstaff")
    @commands.guild_only()
    async def delstaff(self, ctx, role: discord.Role):
        """[STAFF] Removes a role to the staff list"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        exist = await GG.MDB['serverstaff'].find_one({"guild": ctx.guild.id, "roles": int(role.id)})
        if exist is not None:
            await GG.MDB['serverstaff'].delete_one({"guild": ctx.guild.id, "roles": int(role.id)})
            GG.STAFF.remove(int(role.id))
            return await ctx.respond(f"{role.name} was removed from the staff list.", ephemeral=True)
        else:
            return await ctx.respond(f"{role.name} is not on the staff list.", ephemeral=True)

    @slash_command(name="prefix")
    @commands.guild_only()
    async def prefix(self, ctx, prefix: Option(str, "What do you want the prefix to be")):
        """[STAFF] Sets the bot's prefix for this server. Forgot the prefix? Reset it with "/prefix $"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        guild_id = str(ctx.guild.id)
        if prefix is None:
            current_prefix = await self.bot.get_server_prefix(ctx.message)
            return await ctx.respond(f"My current prefix is: `{current_prefix}`", ephemeral=True)

        self.bot.prefixes[guild_id] = prefix

        await self.bot.mdb.prefixes.update_one(
            {"guild_id": guild_id},
            {"$set": {"prefix": prefix}},
            upsert=True
        )

        return await ctx.respond("Prefix set to `{}` for this server.".format(prefix), ephemeral=True)

    @slash_command(name="appealurl")
    @commands.guild_only()
    async def appealurl(self, ctx, appeal_url: Option(str, "The appeal.gg URL for this server")):
        """[STAFF] Sets the appeal.gg URL suffix included in ban DMs."""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        appeal_url = extract_appeal_path(appeal_url)
        if not appeal_url:
            return await ctx.respond("Enter an appeal.gg URL or URL path.", ephemeral=True)
        full_appeal_url = f"https://appeal.gg/{appeal_url}"

        await GG.MDB['bot_settings'].update_one(
            {"guild": ctx.guild.id},
            {"$set": {"appeal_url": appeal_url}},
            upsert=True
        )
        return await ctx.respond(f"Appeal URL set for this server: {full_appeal_url}", ephemeral=True)

    @slash_command(name="addchannel")
    @commands.guild_only()
    async def addchannel(self, ctx, channeltype: Option(str, "Choose your channel type", choices=categories), channel: Option(discord.TextChannel, "For which channel do you want to set the type?")):
        """[STAFF] Gives a channel a specific type."""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        channelExists = await GG.MDB['channelinfo'].find_one({"channel": channel.id})
        if channelExists is not None:
            return await ctx.respond(f"{channel.name} is already on the special channel list.", ephemeral=True)
        else:
            await GG.MDB['channelinfo'].insert_one({"guild": ctx.guild.id, "channel": channel.id, "type": channeltype})
            GG.CHANNEL[channel.id] = str(channeltype)
            return await ctx.respond(f"{channel.name} was added to the special channel list as {channeltype}", ephemeral=True)

    @slash_command(name="delchannel")
    @commands.guild_only()
    async def delchannel(self, ctx, channel: Option(discord.TextChannel, "From what channel do you want to remove the channel type?")):
        """[STAFF] Removes the type of a channel, reverting it to a "normal" channel"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        channelExists = await GG.MDB['channelinfo'].find_one({"channel": channel.id})
        if channelExists is not None:
            await GG.MDB['channelinfo'].delete_one({"channel": channel.id})
            del GG.CHANNEL[channel.id]
            await ctx.send(f"{channel.name} was removed from the special channel list.")
        else:
            await ctx.send(f"{channel.name} is not on the special channel list.")


def setup(bot):
    log.info("[Cog] ServerCommands")
    bot.add_cog(ServerCommands(bot))
