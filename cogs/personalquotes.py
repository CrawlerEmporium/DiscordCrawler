import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

import utils.globals as GG
from DBService import DBService
from utils import logger

log = logger.logger


def personal_embed(db_response, author):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response[2], color=author.color)
    else:
        embed = discord.Embed(description=db_response[2])
    embed.set_author(name=str(author), icon_url=author.avatar_url)
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
    embed.set_footer(text='Personal Quote')
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


class PersonalQuotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['padd'])
    async def personaladd(self, ctx, trigger, *, response=None):
        """Adds a personal quote."""
        if not response and not ctx.message.attachments:
            return await ctx.send(
                content=":x:" + ' **You must include at least a response or an attachment in your message.**')
        else:
            try:
                DBService.exec("INSERT INTO PersonalQuotes (User, Trigger" + (", Response" if response else "") + (
                    ", Attachments" if ctx.message.attachments else "") + ") VALUES (" + str(
                    ctx.author.id) + ", '" + trigger.replace('\'', '\'\'') + "'" + (
                                   ", '" + response.replace('\'', '\'\'') + "'" if response else "") + (
                                   ", '" + " | ".join(
                                       [attachment.url for attachment in ctx.message.attachments]).replace('\'',
                                                                                                           '\'\'') + "'" if ctx.message.attachments else "") + ")")
            except Exception:
                return await ctx.send(content=":x:" + ' **You already have a quote with that trigger.**')

        await ctx.send(content=":white_check_mark:" + ' **Quote added.**')
        await GG.upCommand("padd")

    @commands.command(aliases=['premove', 'prem'])
    async def personalremove(self, ctx, *, trigger):
        """Removes a personal quote."""
        user_quote = DBService.exec(
            "SELECT * FROM PersonalQuotes WHERE User = " + str(ctx.author.id) + " AND Trigger = '" + trigger.replace(
                '\'', '\'\'') + "'").fetchone()
        if user_quote:
            DBService.exec(
                "DELETE FROM PersonalQuotes WHERE User = " + str(ctx.author.id) + " AND Trigger = '" + trigger.replace(
                    '\'', '\'\'') + "'")
            await ctx.send(content=":white_check_mark:" + ' **Quote deleted.**')
        else:
            await ctx.send(content=":x:" + ' **Quote with that trigger does not exist.**')
        await GG.upCommand("prem")

    @commands.command(aliases=['p'])
    async def personal(self, ctx, *, trigger):
        """Returns your chosen personal quote."""
        user_quote = DBService.exec(
            "SELECT * FROM PersonalQuotes WHERE User = " + str(ctx.author.id) + " AND Trigger = '" + trigger.replace(
                '\'', '\'\'') + "'").fetchone()
        if not user_quote:
            await ctx.send(content=":x:" + ' **Quote with that trigger does not exist.**')
        else:
            if ctx.guild and ctx.guild.me.permissions_in(
                    ctx.channel).manage_messages:
                await ctx.message.delete()

            await ctx.send(embed=personal_embed(user_quote, ctx.author))
        await GG.upCommand("p")

    @commands.command(aliases=['plist'])
    async def personallist(self, ctx):
        """Returns all your personal quotes."""
        user_quotes = DBService.exec(
            "SELECT * FROM PersonalQuotes WHERE User = " + str(ctx.author.id)).fetchall()
        if len(user_quotes) == 0:
            await ctx.send(content=":x:" + ' **You have no personal quotes**')
        else:
            embeds = list_embed(user_quotes, ctx.author)
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
        await GG.upCommand("plist")

    @commands.command(aliases=['pclear'])
    async def personalclear(self, ctx):
        """Deletes **ALL** your personal quotes."""
        DBService.exec("DELETE FROM PersonalQuotes WHERE User = " + str(ctx.author.id))
        await ctx.send(content=":white_check_mark:" + ' **Cleared all your personal quotes.**')
        await GG.upCommand("pclear")


def setup(bot):
    log.info("Loading PersonalQuotes Cog...")
    bot.add_cog(PersonalQuotes(bot))
