import discord
import math

from DBService import DBService
from disputils import BotEmbedPaginator
from discord.ext import commands
from utils import logger
import utils.globals as GG

log = logger.logger


def global_embed(self, db_response, author, message, command):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response[2], color=author.color)
    else:
        embed = discord.Embed(description=db_response[2])
    embed.set_author(name=str(author), icon_url=author.avatar_url)
    embed.title = command
    if db_response[3] != None:
        attachments = db_response[3].split(' | ')
        if len(attachments) == 1 and (
                attachments[0].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webp', '.bmp')) or
                attachments[0].lower().startswith('https://chart.googleapis.com/chart?')):
            embed.set_image(url=attachments[0])
        else:
            attachment_count = 0
            for attachment in attachments:
                attachment_count += 1
                embed.add_field(name='Attachment ' + str(attachment_count), value=attachment, inline=False)
    embed.set_footer(text=f'You too can use this command. ``{self.bot.get_server_prefix(message)}g {command}``')
    return embed


def list_embed(list_personals, author):
    embedList = []
    for i in range(0, len(list_personals), 10):
        lst = list_personals[i:i + 10]
        desc = "** **"
        for item in lst:
            desc = '\n'.join('• `' + item[1] + '`')
        if isinstance(author, discord.Member) and author.color != discord.Colour.default():
            embed = discord.Embed(description=desc, color=author.color)
        else:
            embed = discord.Embed(description=desc)
        embed.set_author(name='Personal Quotes', icon_url=author.avatar_url)
        embedList.append(embed)
    return embedList


class GlobalCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['gadd'], hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def globaladd(self, ctx, trigger, *, response=None):
        """Adds a global command."""
        if not response and not ctx.message.attachments:
            return await ctx.send(
                content=":x:" + ' **You must include at least a response or an attachment in your message.**')
        else:
            try:
                DBService.exec("INSERT INTO GlobalCommands (Guild, Trigger" + (", Response" if response else "") + (
                                    ", Attachments" if ctx.message.attachments else "") + ") VALUES (" + str(
                                    ctx.message.guild.id) + ", '" + trigger.replace('\'','\'\'') + "'" + (
                                   ", '" + response.replace('\'', '\'\'') + "'" if response else "") + (
                                   ", '" + " | ".join(
                                       [attachment.url for attachment in ctx.message.attachments]).replace('\'',
                                                                                                           '\'\'') + "'" if ctx.message.attachments else "") + ")")
            except Exception:
                return await ctx.send(content=":x:" + ' **This server already has a command with that trigger.**')

        await ctx.send(content=":white_check_mark:" + ' **Command added.**')
        await GG.upCommand("gadd")

    @commands.command(aliases=['gremove', 'grem'], hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def globalremove(self, ctx, *, trigger):
        """Removes a global command."""
        user_quote = DBService.exec(
            "SELECT * FROM GlobalCommands WHERE Guild = " + str(ctx.message.guild.id) + " AND Trigger = '" + trigger.replace(
                '\'', '\'\'') + "'").fetchone()
        if user_quote:
            DBService.exec(
                "DELETE FROM GlobalCommands WHERE Guild = " + str(ctx.message.guild.id) + " AND Trigger = '" + trigger.replace(
                    '\'', '\'\'') + "'")
            await ctx.send(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        await GG.upCommand("grem")

    @commands.command(aliases=['g','gc','giddy'])
    @commands.guild_only()
    async def globalcommand(self, ctx, *, trigger):
        """Returns your chosen global command."""
        trig = trigger.replace('\'', '\'\'')
        user_quote = DBService.exec(
            "SELECT * FROM GlobalCommands WHERE Guild = " + str(ctx.message.guild.id) + " AND Trigger = '" + trig + "'").fetchone()
        if not user_quote:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.guild and ctx.guild.me.permissions_in(
                    ctx.channel).manage_messages:
                await ctx.message.delete()

            await ctx.send(embed=global_embed(self, user_quote, ctx.author, ctx.message, trig))
        await GG.upCommand("g")

    @commands.command(aliases=['glist'])
    @commands.guild_only()
    async def globallist(self, ctx, page_number: int = 1):
        """Returns all global commands."""
        user_quotes = DBService.exec(
            "SELECT * FROM GlobalCommands WHERE Guild = " + str(ctx.message.guild.id)).fetchall()
        if len(user_quotes) == 0:
            await ctx.send(content=":x:" + ' **You have no global quotes**')
        else:
            embeds = list_embed(user_quotes, ctx.author)
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
        await GG.upCommand("glist")


def setup(bot):
    log.info("Loading Global Commands Cog...")
    bot.add_cog(GlobalCommands(bot))
