import io
import json

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

    names = GG.LOCALIZATION['personalquotes']['name']
    descriptions = GG.LOCALIZATION['personalquotes']['description']

    personal = SlashCommandGroup("personal", "All your personal quotes")

    @personal.command(description=descriptions['quote']['en-US'], name_localizations=names['quote'], description_localizations=descriptions['quote'])
    async def quote(self, ctx, quote: Option(str, description=descriptions['quote.quote']['en-US'], autocomplete=get_quote, name_localizations=names['quote.quote'], description_localizations=descriptions['quote.quote'])):
        user_quote = await GG.MDB['personalcommands'].find_one({"user": ctx.interaction.user.id, "trigger": quote})
        await self.sendPersonalChoice(ctx, user_quote)

    @personal.command(description=descriptions['clear']['en-US'], name_localizations=names['clear'], description_localizations=descriptions['clear'])
    async def clear(self, ctx):
        await GG.MDB['personalcommands'].delete_many({"user": ctx.interaction.user.id})
        await ctx.respond(content=":white_check_mark:" + ' **Cleared all your personal quotes.**')

    @personal.command(description=descriptions['code']['en-US'], name_localizations=names['code'], description_localizations=descriptions['code'])
    async def code(self, ctx, quote: Option(str, autocomplete=get_quote, description=descriptions['code.quote']['en-US'],  name_localizations=names['code.quote'], description_localizations=descriptions['code.quote'])):
        user_quote = await GG.MDB['personalcommands'].find_one({"user": ctx.interaction.user.id, "trigger": quote})
        replaceString = '\`'
        await ctx.respond(f"```{user_quote['response'].replace('`', replaceString)}```", files=user_quote['attachments'])

    @personal.command(description=descriptions['add']['en-US'], name_localizations=names['add'], description_localizations=descriptions['add'])
    async def add(self, ctx,
                  quote: Option(str, description=descriptions['add.quote']['en-US'], name_localizations=names['add.quote'], description_localizations=descriptions['add.quote']),
                  response: Option(str, description=descriptions['add.response']['en-US'], name_localizations=names['add.response'], description_localizations=descriptions['add.response']),
                  attachment: Option(discord.Attachment, required=False, description=descriptions['add.attachment']['en-US'], name_localizations=names['add.attachment'], description_localizations=descriptions['add.attachment'])):
        checkIfExist = await GG.MDB['personalcommands'].find_one({"user": ctx.interaction.user.id, "trigger": quote})
        if checkIfExist is not None:
            return await ctx.respond(content=":x:" + ' **You already have a command with that trigger.**')
        else:
            if attachment is not None:
                await GG.MDB['personalcommands'].insert_one({"user": ctx.interaction.user.id, "trigger": quote, "response": response, "attachments": [attachment.url]})
            else:
                await GG.MDB['personalcommands'].insert_one({"user": ctx.interaction.user.id, "trigger": quote, "response": response, "attachments": []})

        await ctx.respond(content=":white_check_mark:" + ' **Command added.**')

    @personal.command(description=descriptions['delete']['en-US'], name_localizations=names['delete'], description_localizations=descriptions['delete'])
    async def delete(self, ctx, quote: Option(str, autocomplete=get_quote, description=descriptions['delete.quote']['en-US'], name_localizations=names['delete.quote'], description_localizations=descriptions['delete.quote'])):
        result = await GG.MDB['personalcommands'].delete_one(
            {"user": ctx.interaction.user.id, "trigger": quote.replace('\'', '\'\'')})
        if result.deleted_count > 0:
            await ctx.respond(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.respond(content=":x:" + ' **Command with that trigger does not exist.**')

    @personal.command(description=descriptions['list']['en-US'], name_localizations=names['list'], description_localizations=descriptions['list'])
    async def list(self, ctx):
        user_quotes = await GG.MDB['personalcommands'].find({"user": ctx.interaction.user.id}).to_list(length=None)
        if len(user_quotes) == 0:
            await ctx.respond(content=":x:" + ' **You have no personal commands**')
        else:
            choices = [(r['trigger'], r) for r in user_quotes]
            choice = await get_selection(ctx, choices, title=f"Personal Quotes for {ctx.interaction.user}", author=True)
            await self.sendPersonalChoice(ctx, choice)

    async def sendPersonalChoice(self, ctx, user_quote):
        if user_quote is not None:  # Check for the personalList action, as it can return the stop button
            embed, attachments = personal_embed(user_quote, ctx.interaction.user)
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
