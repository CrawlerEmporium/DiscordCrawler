import io

import discord
import requests
from discord import SlashCommandGroup, Option, AutocompleteContext
from discord.ext import commands

import utils.globals as GG
from crawler_utilities.handlers import logger
from crawler_utilities.utils.functions import try_delete

# noinspection PyUnresolvedReferences
from crawler_utilities.utils.pagination import get_selection

log = logger.logger


def personal_embed(db_response, author):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response['response'], color=author.color)
    else:
        embed = discord.Embed(description=db_response['response'])
    embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text='Personal Quote')
    return embed, db_response['attachments']


async def get_quote(ctx: AutocompleteContext):
    db = await GG.MDB['personalcommands'].find({"user": ctx.interaction.user.id}).to_list(length=None)
    return [item['trigger'] for item in db if ctx.value.lower() in item['trigger']]


class PersonalQuotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    personal = SlashCommandGroup("personal", "All your personal quotes")

    @personal.command()
    async def quote(self, ctx, trigger: Option(str, "Which personal quote do you want to post?", autocomplete=get_quote)):
        """Returns your chosen personal quote."""
        user_quote = await GG.MDB['personalcommands'].find_one({"user": ctx.message.author.id, "trigger": trigger})
        await self.sendPersonalChoice(ctx, user_quote)

    @personal.command()
    async def clear(self, ctx):
        """Deletes **ALL** your personal quotes."""
        await GG.MDB['personalcommands'].delete_many({"user": ctx.message.author.id})
        await ctx.respond(content=":white_check_mark:" + ' **Cleared all your personal quotes.**')

    @personal.command()
    async def code(self, ctx, trigger: Option(str, "For which personal quote do you want to see the code?", autocomplete=get_quote)):
        """Returns your chosen personal quote in code."""
        user_quote = await GG.MDB['personalcommands'].find_one({"user": ctx.message.author.id, "trigger": trigger})
        replaceString = '\`'
        await ctx.respond(f"```{user_quote['response'].replace('`', replaceString)}```", files=user_quote['attachments'])

    @personal.command()
    async def add(self, ctx, trigger, *, response=None):
        """Adds a personal quote."""
        if not response and not ctx.message.attachments:
            return await ctx.respond(
                content=":x:" + ' **You must include at least a response or an attachment in your message.**')
        else:
            trig = trigger
            if response is not None:
                response = response
            checkIfExist = await GG.MDB['personalcommands'].find_one({"user": ctx.message.author.id, "trigger": trig})
            if checkIfExist is not None:
                return await ctx.respond(content=":x:" + ' **You already have a command with that trigger.**')
            else:
                await GG.MDB['personalcommands'].insert_one(
                    {"user": ctx.message.author.id, "trigger": trig, "response": response,
                     "attachments": [attachment.url for attachment in ctx.message.attachments]})

        await ctx.respond(content=":white_check_mark:" + ' **Command added.**')

    @personal.command()
    async def delete(self, ctx, trigger: Option(str, "Which personal quote do you want to delete?", autocomplete=get_quote)):
        """Removes a personal quote."""
        result = await GG.MDB['personalcommands'].delete_one(
            {"user": ctx.message.author.id, "trigger": trigger.replace('\'', '\'\'')})
        if result.deleted_count > 0:
            await ctx.respond(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.respond(content=":x:" + ' **Command with that trigger does not exist.**')

    @personal.command()
    async def list(self, ctx):
        """Returns all your personal quotes."""
        user_quotes = await GG.MDB['personalcommands'].find({"user": ctx.interaction.user.id}).to_list(length=None)
        if len(user_quotes) == 0:
            await ctx.respond(content=":x:" + ' **You have no personal commands**')
        else:
            choices = [(r['trigger'], r) for r in user_quotes]
            choice = await get_selection(ctx, choices, title=f"Personal Quotes for {ctx.author}", author=True)
            await self.sendPersonalChoice(ctx, choice)

    async def sendPersonalChoice(self, ctx, user_quote):
        if user_quote is not None:  # Check for the personalList action, as it can return the stop button
            embed, attachments = personal_embed(user_quote, ctx.author)
            files = []
            if attachments != None:
                if len(attachments) == 1 and (
                        attachments[0].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webp', '.bmp')) or
                        attachments[0].lower().startswith('https://chart.googleapis.com/chart?')):
                    embed.set_image(url=attachments[0])
                else:
                    for attachment in attachments:
                        url = attachment
                        file = requests.get(url)
                        bitties = io.BytesIO(file.content)
                        bitties.seek(0)
                        dFile = discord.File(bitties, filename=url.rsplit('/', 1)[-1])
                        files.append(dFile)
            await ctx.respond(embed=embed, files=files)


def setup(bot):
    log.info("[Cog] PersonalQuotes")
    bot.add_cog(PersonalQuotes(bot))
