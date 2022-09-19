import io

import discord
import requests
from discord import AutocompleteContext, SlashCommandGroup, Option, slash_command

from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs
from crawler_utilities.utils.embeds import EmbedWithAuthor
# noinspection PyUnresolvedReferences
from crawler_utilities.utils.pagination import get_selection
from discord.ext import commands
import utils.globals as GG

log = GG.log


def global_embed(ctx, quote, whisper):
    embed = EmbedWithAuthor(ctx)
    embed.colour = ctx.author.color
    response = f"{quote['Response']}"
    embed.description = response.replace('\\n', '\n')
    if not whisper:
        embed.set_footer(text=f'You too can use this command. /global quote:{quote["Trigger"]}')
    else:
        embed.set_footer(text=f'This command was triggered in {ctx.interaction.guild}. You can trigger it there by running /whisper quote:{quote["Trigger"]}')
    attachments = quote.get("Attachments", [])
    return embed, attachments


async def get_quote(ctx: AutocompleteContext):
    db = await GG.MDB['globalcommands'].find({"Guild": ctx.interaction.guild_id}).to_list(length=None)
    return [item['Trigger'] for item in db if ctx.value.lower() in item['Trigger']]


class GlobalCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = 'globalcommands'
    personal = SlashCommandGroup("global", "All quotes specifically for this server")

    @personal.command(**get_command_kwargs(cogName, "quote"))
    @commands.guild_only()
    async def quote(self, ctx, quote: Option(str, autocomplete=get_quote, **get_parameter_kwargs(cogName, "quote.quote"))):
        """Returns your chosen global command."""
        global_quote = await GG.MDB['globalcommands'].find_one({"Guild": ctx.interaction.guild_id, "Trigger": quote})
        await self.send_global_quote(ctx, global_quote)

    @personal.command(**get_command_kwargs(cogName, "code"))
    @commands.guild_only()
    async def code(self, ctx, quote: Option(str, autocomplete=get_quote, **get_parameter_kwargs(cogName, "code.quote"))):
        user_quote = await GG.MDB['globalcommands'].find_one({"Guild": ctx.interaction.guild_id, "Trigger": quote})
        replaceString = '\`'
        await ctx.respond(f"```{user_quote['Response'].replace('`', replaceString)}```", files=user_quote['Attachments'])

    @personal.command(**get_command_kwargs(cogName, "list"))
    @commands.guild_only()
    async def list(self, ctx):
        await ctx.defer()
        user_quotes = await GG.MDB['globalcommands'].find({"Guild": ctx.interaction.guild_id}).to_list(length=None)
        if len(user_quotes) == 0:
            await ctx.respond(content=":x:" + ' **There are no global commands for this server**')
        else:
            choices = [(r['Trigger'], r) for r in user_quotes]
            choice = await get_selection(ctx, choices, title=f"Global Quotes for {ctx.interaction.guild}", author=True)
            if choice is not None:
                await self.send_global_quote(ctx, choice)
            else:
                await ctx.respond("Command canceled", delete_after=5)


    @personal.command(**get_command_kwargs(cogName, "add"))
    @commands.guild_only()
    @discord.default_permissions(
        manage_messages=True,
    )
    async def add(self, ctx,
                  quote: Option(str, **get_parameter_kwargs(cogName, "add.quote")),
                  response: Option(str, **get_parameter_kwargs(cogName, "add.response")),
                  attachment: Option(discord.Attachment, required=False, **get_parameter_kwargs(cogName, "add.attachment"))):
        checkIfExist = await GG.MDB['globalcommands'].find_one({"Guild": ctx.interaction.guild_id, "Trigger": quote})
        if checkIfExist is not None:
            return await ctx.respond(content=":x:" + ' **You already have a command with that trigger.**')
        else:
            if attachment is not None:
                await GG.MDB['globalcommands'].insert_one({"Guild": ctx.interaction.guild_id, "Trigger": quote, "Response": response, "Attachments": [attachment.url]})
            else:
                await GG.MDB['globalcommands'].insert_one({"Guild": ctx.interaction.guild_id, "Trigger": quote, "Response": response, "Attachments": []})

        await ctx.respond(content=":white_check_mark:" + ' **Command added.**')

    @personal.command(**get_command_kwargs(cogName, "delete"))
    @commands.guild_only()
    @discord.default_permissions(
        manage_messages=True,
    )
    async def delete(self, ctx, quote: Option(str, autocomplete=get_quote, **get_parameter_kwargs(cogName, "delete.quote"))):
        result = await GG.MDB['globalcommands'].delete_one({"Guild": ctx.interaction.guild_id, "Trigger": quote.replace('\'', '\'\'')})
        if result.deleted_count > 0:
            await ctx.respond(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.respond(content=":x:" + ' **Command with that trigger does not exist.**')

    @slash_command(name="whisper")
    @commands.guild_only()
    async def whisper(self, ctx, quote: Option(str, autocomplete=get_quote, description="Which quote do you want?")):
        """Returns your chosen global command. But silent"""
        global_quote = await GG.MDB['globalcommands'].find_one({"Guild": ctx.interaction.guild_id, "Trigger": quote})
        await self.send_global_quote(ctx, global_quote, True)

    async def send_global_quote(self, ctx, global_quote, whisper=False):
        embed, attachments = global_embed(ctx, global_quote, whisper)
        files = []
        if attachments is not None:
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
        if not whisper:
            await ctx.respond(embed=embed, files=files)
        else:
            await ctx.respond(embed=embed, files=files, ephemeral=True)


def setup(bot):
    log.info("[Cog] Global Commands")
    bot.add_cog(GlobalCommands(bot))
