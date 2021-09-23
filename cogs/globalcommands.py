import typing

import discord

# noinspection PyUnresolvedReferences
from crawler_utilities.utils.pagination import get_selection
from discord.ext import commands
from crawler_utilities.handlers import logger
import utils.globals as GG
from crawler_utilities.utils.functions import try_delete

log = logger.logger


async def global_embed(self, db_response, ctx, command, server=None, whisper=False):
    if isinstance(ctx.author, discord.Member) and ctx.author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response['Response'], color=ctx.author.color)
    else:
        embed = discord.Embed(description=db_response['Response'])
    if db_response['Attachments'] != None:
        attachments = db_response['Attachments']
        if len(attachments) == 1 and (
                attachments[0].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webp', '.bmp')) or
                attachments[0].lower().startswith('https://chart.googleapis.com/chart?')):
            embed.set_image(url=attachments[0])
        else:
            attachment_count = 0
            for attachment in attachments:
                attachment_count += 1
                embed.add_field(name='Attachment ' + str(attachment_count), value=attachment, inline=False)
    prefix = await self.bot.get_server_prefix(ctx.message)
    if not whisper:
        embed.set_footer(text=f'You too can use this command. {prefix}g {command}')
    else:
        embed.set_footer(text=f'This command was triggered in {server}. You can trigger it there by running {prefix}g {command}')
    return embed


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
            trig = trigger
            if response is not None:
                response = response
            checkIfExist = await GG.MDB['globalcommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
            if checkIfExist is not None:
                return await ctx.send(content=":x:" + ' **This server already has a command with that trigger.**')
            else:
                await GG.MDB['globalcommands'].insert_one({"Guild": ctx.message.guild.id, "Trigger": trig, "Response": response, "Attachments": [attachment.url for attachment in ctx.message.attachments]})
        await ctx.send(content=":white_check_mark:" + ' **Command added.**')

    @commands.command(aliases=['gremove', 'grem'], hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def globalremove(self, ctx, trigger):
        """Removes a global command."""
        result = await GG.MDB['globalcommands'].delete_one({"Guild": ctx.message.guild.id, "Trigger": trigger.replace('\'', '\'\'')})
        if result.deleted_count > 0:
            await ctx.send(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')

    @commands.command(aliases=['g'])
    @commands.guild_only()
    async def globalcommand(self, ctx, trigger, member: typing.Optional[discord.Member] = None):
        """Returns your chosen global command."""
        trig = trigger
        user_quote = await GG.MDB['globalcommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
        if user_quote is None:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await try_delete(ctx.message)

            if member is not None:
                await ctx.send(content=member.mention, embed=await global_embed(self, user_quote, ctx, trig))
            else:
                await ctx.send(embed=await global_embed(self, user_quote, ctx, trig))

    @commands.command(aliases=['w'])
    @commands.guild_only()
    async def whispercommand(self, ctx, trigger, member: typing.Optional[discord.Member] = None):
        """Returns your chosen global command."""
        trig = trigger
        user_quote = await GG.MDB['globalcommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
        if ctx.author.dm_channel is not None:
            DM = ctx.author.dm_channel
        else:
            DM = await ctx.author.create_dm()

        if member is not None:
            if member.dm_channel is not None:
                DM = member.dm_channel
            else:
                DM = await member.create_dm()

        if user_quote is None:
            try:
                await DM.send(content=":x:" + ' **Command with that trigger does not exist.**')
            except discord.Forbidden:
                if member is not None:
                    await ctx.send(f"{ctx.author.mention} I tried DMing {member.mention}, they either blocked me, or they don't allow DM's")
                else:
                    await ctx.send(f"{ctx.author.mention} I tried DMing you, but you either blocked me, or you don't allow DM's")
        else:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await try_delete(ctx.message)
            try:
                await DM.send(embed=await global_embed(self, user_quote, ctx, trig, ctx.guild.name, True))
            except discord.Forbidden:
                if member is not None:
                    await ctx.send(f"{ctx.author.mention} I tried DMing {member.mention}, they either blocked me, or they don't allow DM's")
                else:
                    await ctx.send(f"{ctx.author.mention} I tried DMing you, but you either blocked me, or you don't allow DM's")

    @commands.command(aliases=['glist'])
    @commands.guild_only()
    async def globallist(self, ctx):
        """Returns all global commands."""
        user_quotes = await GG.MDB['globalcommands'].find({"Guild": ctx.message.guild.id}).to_list(length=None)
        if len(user_quotes) == 0:
            await ctx.send(content=":x:" + ' **You have no global quotes**')
        else:
            choices = [(r['Trigger'], r) for r in user_quotes]
            choice = await get_selection(ctx, choices, title=f"Server Commands for {ctx.guild}", author=True)
            if choice is not None:
                await ctx.send(embed=await global_embed(self, choice, ctx, choice['Trigger']))

    @commands.command(aliases=['gc'])
    @commands.guild_only()
    async def globalcode(self, ctx, trigger):
        """Returns your chosen global command."""
        trig = trigger
        user_quote = await GG.MDB['globalcommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
        if user_quote is None:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await try_delete(ctx.message)

            replaceString = '\`'
            await ctx.send(f"```{user_quote['Response'].replace('`', replaceString)}```",
                           files=user_quote['Attachments'])


def setup(bot):
    log.info("[Cog] Global Commands")
    bot.add_cog(GlobalCommands(bot))
