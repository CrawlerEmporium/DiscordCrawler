import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

import utils.globals as GG
from utils import logger
from utils.functions import try_delete

log = logger.logger


def personal_embed(db_response, author):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response['response'], color=author.color)
    else:
        embed = discord.Embed(description=db_response['response'])
    embed.set_author(name=str(author), icon_url=author.avatar_url)
    if db_response['attachments'] != None:
        attachments = db_response['attachments']
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
        desc = ""
        for item in lst:
            desc += '• `' + str(item['trigger']) + '`\n'
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
            trig = trigger
            if response is not None:
                response = response
            checkIfExist = await GG.MDB['personalcommands'].find_one({"user": ctx.message.author.id, "trigger": trig})
            if checkIfExist is not None:
                return await ctx.send(content=":x:" + ' **You already have a command with that trigger.**')
            else:
                await GG.MDB['personalcommands'].insert_one({"user": ctx.message.author.id, "trigger": trig, "response": response, "attachments": [attachment.url for attachment in ctx.message.attachments]})

        await ctx.send(content=":white_check_mark:" + ' **Command added.**')

    @commands.command(aliases=['premove', 'prem'])
    async def personalremove(self, ctx, trigger):
        """Removes a personal quote."""
        result = await GG.MDB['personalcommands'].delete_one({"user": ctx.message.author.id, "trigger": trigger.replace('\'', '\'\'')})
        if result.deleted_count > 0:
            await ctx.send(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')

    @commands.command(aliases=['p'])
    async def personal(self, ctx, trigger):
        """Returns your chosen personal quote."""
        trig = trigger.replace('\'', '\'\'')
        user_quote = await GG.MDB['personalcommands'].find_one({"user": ctx.message.author.id, "trigger": trig})
        if user_quote is None:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.guild and ctx.guild.me.permissions_in(
                    ctx.channel).manage_messages:
                await try_delete(ctx.message)

            await ctx.send(embed=personal_embed(user_quote, ctx.author))

    @commands.command(aliases=['plist'])
    async def personallist(self, ctx):
        """Returns all your personal quotes."""
        user_quotes = await GG.MDB['personalcommands'].find({"user": ctx.message.author.id}).to_list(length=None)
        if len(user_quotes) == 0:
            await ctx.send(content=":x:" + ' **You have no personal commands**')
        else:
            embeds = list_embed(user_quotes, ctx.author)
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()

    @commands.command(aliases=['pclear'])
    async def personalclear(self, ctx):
        """Deletes **ALL** your personal quotes."""
        await GG.MDB['personalcommands'].delete_many({"user": ctx.message.author.id})
        await ctx.send(content=":white_check_mark:" + ' **Cleared all your personal quotes.**')

    @commands.command(aliases=['pc'])
    async def personalcode(self, ctx, trigger):
        """Returns your chosen global command."""
        trig = trigger
        user_quote = await GG.MDB['personalcommands'].find_one({"user": ctx.message.author.id, "trigger": trig})
        if user_quote is None:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.guild and ctx.guild.me.permissions_in(ctx.channel).manage_messages:
                await try_delete(ctx.message)

            await ctx.send(f"```{user_quote['response']}```", files=user_quote['attachments'])


def setup(bot):
    log.info("[Cog] PersonalQuotes")
    bot.add_cog(PersonalQuotes(bot))
