import typing

import discord

# noinspection PyUnresolvedReferences
from crawler_utilities.utils.pagination import get_selection
from discord.ext import commands
import utils.globals as GG
from crawler_utilities.utils.functions import try_delete

log = GG.log


def global_embed(db_response, author):
    if isinstance(author, discord.Member) and author.color != discord.Colour.default():
        embed = discord.Embed(description=db_response['Response'], color=author.color)
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
    return embed


class DeleteCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['dadd'], hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def deleteadd(self, ctx, trigger, *, response=None):
        """Adds a global command."""
        if not response and not ctx.message.attachments:
            return await ctx.send(
                content=":x:" + ' **You must include at least a response or an attachment in your message.**')
        else:
            trig = trigger
            if response is not None:
                response = response
            checkIfExist = await GG.MDB['deletecommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
            if checkIfExist is not None:
                return await ctx.send(content=":x:" + ' **This server already has a command with that trigger.**')
            else:
                await GG.MDB['deletecommands'].insert_one(
                    {"Guild": ctx.message.guild.id, "Trigger": trig, "Response": response,
                     "Attachments": [attachment.url for attachment in ctx.message.attachments]})
        await ctx.send(content=":white_check_mark:" + ' **Command added.**')

    @commands.command(aliases=['dremove', 'drem'], hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def deleteremove(self, ctx, trigger):
        """Removes a global command."""
        result = await GG.MDB['deletecommands'].delete_one(
            {"Guild": ctx.message.guild.id, "Trigger": trigger.replace('\'', '\'\'')})
        if result.deleted_count > 0:
            await ctx.send(content=":white_check_mark:" + ' **Command deleted.**')
        else:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')

    @commands.command(aliases=['d'])
    @GG.is_staff()
    @commands.guild_only()
    async def deletecommand(self, ctx, trigger, message: typing.Optional[discord.Message] = None):
        """Returns your chosen global command."""
        await try_delete(ctx.message)
        trig = trigger
        user_quote = await GG.MDB['deletecommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
        if user_quote is None:
            msg = await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
            await msg.delete(delay=10)
        else:
            if message.author is not None:
                if type(message.author) == discord.Member:
                    if message.author.guild_permissions.administrator:
                        return await ctx.send("You are not allowed to delete messages from admins this way.")

                    if message.author.dm_channel is not None:
                        DM = message.author.dm_channel
                    else:
                        DM = await message.author.create_dm()

                await message.delete()
                try:
                    await DM.send(embed=global_embed(user_quote, ctx.author))
                except discord.Forbidden:
                    if message.author is not None:
                        await ctx.send(
                            f"{ctx.author.mention} I tried DMing {message.author.mention}, they either blocked me, or they don't allow DM's")
                    else:
                        await ctx.send(
                            f"{ctx.author.mention} I tried DMing you, but you either blocked me, or you don't allow DM's")
            else:
                return await message.delete()

    @commands.command(aliases=['dlist'])
    @GG.is_staff()
    @commands.guild_only()
    async def deletelist(self, ctx):
        """Returns all global commands."""
        user_quotes = await GG.MDB['deletecommands'].find({"Guild": ctx.message.guild.id}).to_list(length=None)
        if len(user_quotes) == 0:
            await ctx.send(content=":x:" + ' **You have no global quotes**')
        else:
            choices = [(r['Trigger'], r) for r in user_quotes]
            choice = await get_selection(ctx, choices, title=f"Delete Commands for {ctx.guild}", author=True)
            await ctx.channel.send(embed=global_embed(choice, ctx.author))

    @commands.command(aliases=['dc'])
    @GG.is_staff()
    @commands.guild_only()
    async def deletecode(self, ctx, trigger):
        """Returns your chosen global command."""
        trig = trigger
        user_quote = await GG.MDB['deletecommands'].find_one({"Guild": ctx.message.guild.id, "Trigger": trig})
        if user_quote is None:
            await ctx.send(content=":x:" + ' **Command with that trigger does not exist.**')
        else:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await try_delete(ctx.message)

            await ctx.send(f"```{user_quote['Response']}```", files=user_quote['Attachments'])


def setup(bot):
    log.info("[Cog] Delete Commands")
    bot.add_cog(DeleteCommands(bot))
