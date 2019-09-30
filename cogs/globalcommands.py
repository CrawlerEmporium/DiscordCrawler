import discord
from DBService import DBService
from discord.ext import commands
from utils import logger
import utils.globals as GG

log = logger.logger


def global_embed(db_response, author):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response[1], color=author.color)
    else:
        embed = discord.Embed(description=db_response[1])
    embed.set_author(name=str(author), icon_url=author.avatar_url)
    if db_response[2] != None:
        attachments = db_response[2].split(' | ')
        if len(attachments) == 1 and (
                attachments[0].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webp', '.bmp')) or
                attachments[0].lower().startswith('https://chart.googleapis.com/chart?')):
            embed.set_image(url=attachments[0])
        else:
            attachment_count = 0
            for attachment in attachments:
                attachment_count += 1
                embed.add_field(name='Attachment ' + str(attachment_count), value=attachment, inline=False)
    return embed


def list_embed(list_personals, author, page_number):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description='\n'.join(['• `' + i[1] + '`' for i in list_personals]), color=author.color)
    else:
        embed = discord.Embed(description='\n'.join(['• `' + i[1] + '`' for i in list_personals]))
    embed.set_footer(text='Page: ' + str(page_number))
    return embed


class GlobalCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['gadd'], hidden=True)
    @commands.is_owner()
    async def globaladd(self, ctx, trigger, *, response=None):
        """Adds a global command."""
        if not response and not ctx.message.attachments:
            return await ctx.send(
                content=":x:" + ' **You must include at least a response or an attachment in your message.**')
        else:
            try:
                DBService.exec("INSERT INTO GlobalCommands (Trigger" + (", Response" if response else "") + (
                    ", Attachments" if ctx.message.attachments else "") + ") VALUES (" + "'" + trigger.replace('\'',
                                                                                                               '\'\'') + "'" + (
                                   ", '" + response.replace('\'', '\'\'') + "'" if response else "") + (
                                   ", '" + " | ".join(
                                       [attachment.url for attachment in ctx.message.attachments]).replace('\'',
                                                                                                           '\'\'') + "'" if ctx.message.attachments else "") + ")")
            except Exception:
                return await ctx.send(content=":x:" + ' **You already have a command with that trigger.**')

        await ctx.send(content=":white_check_mark:" + ' **Command added.**')
        await GG.upCommand("gadd")

    @commands.command(aliases=['gremove', 'grem'], hidden=True)
    @commands.is_owner()
    async def globalremove(self, ctx, *, trigger):
        """Removes a global command."""
        user_quote = DBService.exec(
            "SELECT * FROM GlobalCommands WHERE Trigger = '" + trigger.replace(
                '\'', '\'\'') + "'").fetchone()
        if user_quote:
            DBService.exec(
                "DELETE FROM GlobalCommands WHERE Trigger = '" + trigger.replace(
                    '\'', '\'\'') + "'")
            await ctx.send(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        await GG.upCommand("grem")

    @commands.command(aliases=['g'])
    async def globalcommand(self, ctx, *, trigger):
        """Returns your chosen global command."""
        user_quote = DBService.exec(
            "SELECT * FROM GlobalCommands WHERE Trigger = '" + trigger.replace(
                '\'', '\'\'') + "'").fetchone()
        if not user_quote:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.guild and ctx.guild.me.permissions_in(
                    ctx.channel).manage_messages:
                await ctx.message.delete()

            await ctx.send(embed=global_embed(user_quote, ctx.author))
        await GG.upCommand("g")

    @commands.command(aliases=['glist'])
    async def globallist(self, ctx, page_number: int = 1):
        """Returns all global commands."""
        user_quotes = DBService.exec(
            "SELECT * FROM GlobalCommands LIMIT 10 OFFSET " + str(
                10 * (page_number - 1))).fetchall()
        if len(user_quotes) == 0:
            await ctx.send(content=":x:" + ' **No global commands on page `' + str(page_number) + '`**')
        else:
            await ctx.send(embed=list_embed(user_quotes, ctx.author, page_number))
        await GG.upCommand("glist")


def setup(bot):
    log.info("Loading Global Commands Cog...")
    bot.add_cog(GlobalCommands(bot))
