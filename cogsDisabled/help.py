import asyncio
import discord
from discord.ext import commands
from utils import globals as GG
from crawler_utilities.utils import logger

log = logger.logger


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx):
        if GG.checkPermission(ctx, "ar"):
            embed = self.helpCommand(ctx)
            message = await ctx.send(embed=embed)
            await message.add_reaction('💬')
            await message.add_reaction('💭')
            await message.add_reaction('❓')
            await message.add_reaction('📘')
            if GG.is_staff_bool(ctx):
                await message.add_reaction('🔒')
            await message.add_reaction('📔')
            await message.add_reaction('❌')

            await self.waitChangeMessage(ctx, message)
        else:
            await ctx.invoke(self.bot.get_command("oldhelp"))

    async def waitChangeMessage(self, ctx, message):
        def check(reaction, user):
            return (user == ctx.message.author and str(reaction.emoji) == '💬') or \
                   (user == ctx.message.author and str(reaction.emoji) == '💭') or \
                   (user == ctx.message.author and str(reaction.emoji) == '❓') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📘') or \
                   (user == ctx.message.author and str(reaction.emoji) == '🔒') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📔') or \
                   (user == ctx.message.author and str(reaction.emoji) == '❌')

        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            if not isinstance(message.channel, discord.DMChannel):
                await message.clear_reactions()
        else:
            embed = None
            staff = False
            if str(reaction.emoji) == '💬':
                embed = self.quoteCommand(ctx)
            if str(reaction.emoji) == '💭':
                embed = self.personalCommand(ctx)
            if str(reaction.emoji) == '❓':
                embed = self.infoCommand(ctx)
            if str(reaction.emoji) == '📘':
                embed = self.dictCommand(ctx)
            if str(reaction.emoji) == '🔒':
                if GG.is_staff_bool(ctx):
                    embed = self.staffCommand(ctx)
                    await message.clear_reactions()
                    await message.add_reaction('📊')  # Poll
                    await message.add_reaction('📖')  # Server commands
                    await message.add_reaction('📝')  # Server quotes
                    # await message.add_reaction('🔇')  # Mute
                    await message.add_reaction('📔')
                    await message.add_reaction('❌')

                    staff = True
                else:
                    pass
            if str(reaction.emoji) == '📔':
                embed = self.helpCommand(ctx)
            if str(reaction.emoji) == '❌':
                await message.delete()
                if not isinstance(message.channel, discord.DMChannel):
                    await ctx.message.delete()
            if embed is not None:
                await message.edit(embed=embed)
                if not isinstance(message.channel, discord.DMChannel):
                    await reaction.remove(user)
                if staff:
                    await self.waitStaffChangeMessage(ctx, message)
                else:
                    await self.waitChangeMessage(ctx, message)

    def helpCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Help command with clickable categories."
        embed.add_field(name='💬', value='Quote')
        embed.add_field(name='💭', value='Personal Quotes')
        embed.add_field(name='📘', value='Dictionary')
        embed.add_field(name='❓', value='Information')
        if GG.is_staff_bool(ctx):
            embed.add_field(name='🔒', value='Staff Commands')
        embed.add_field(name='📔', value='This help message')
        embed.add_field(name='❌', value='Deletes this message')
        embed.set_footer(text='These reactions are available for 60 seconds, afterwards it will stop responding.')
        return embed

    def quoteCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Quoting of other people."
        embed.add_field(name="quote",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[quote|q] [msgId] [reply]``\nAllows you to quote someone else, anywhere in the server.",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    def dictCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Dictionary."
        embed.add_field(name="Dictionary",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[dictionary|dict|define] [term]``\nLooks up the definition of a word.",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    def infoCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "All information commands."
        embed.add_field(name="botinfo",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[botinfo|stats|info]``\nShows information about <@602774912595263490>", inline=False)
        embed.add_field(name="invite",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}invite``\nShows you the invite link and the information about the permissions the bot need.",
                        inline=False)
        embed.add_field(name="serverinfo",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}serverinfo``\nShows info about server this command is executed on.", inline=False)
        embed.add_field(name="support",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}support``\nShows info about the support server and how to join it.", inline=False)
        embed.add_field(name="oldhelp",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}oldhelp``\nShows you the old help command (the one in a giant embed).", inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed


    def personalCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Your own personal quotes in the bot."
        embed.add_field(name='personal', value=f'``{self.bot.get_server_prefix(ctx.message)}[personal|p] <trigger>``\nReturns your chosen personal quote.',
                        inline=False)
        embed.add_field(name='personaladd',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[personaladd|padd] <trigger> [response]``\nAdds a personal quote.',
                        inline=False)
        embed.add_field(name='personalremove',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[personalremove|premove|prem] <trigger>``\nRemoves a personal quote.', inline=False)
        embed.add_field(name='personallist',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[personallist|plist] [page_number=1]``\nReturns all your personal quotes.',
                        inline=False)
        embed.add_field(name='personalclear',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[personalclear|pclear]``\nDeletes **ALL** your personal quotes.',
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    @commands.command(name="staff")
    @GG.is_staff()
    async def staff(self, ctx):
        if GG.checkPermission(ctx, "ar"):
            embed = self.staffCommand(ctx)
            message = await ctx.send(embed=embed)
            await message.add_reaction('📊')  # Poll
            await message.add_reaction('📖')  # Server commands
            await message.add_reaction('📝')  # Server quotes
            # await message.add_reaction('🔇')  # Mute
            await message.add_reaction('📔')
            await message.add_reaction('❌')

            await self.waitStaffChangeMessage(ctx, message)
        else:
            await ctx.invoke(self.bot.get_command("oldhelp"))


    async def waitStaffChangeMessage(self, ctx, message):
        def check(reaction, user):
            return (user == ctx.message.author and str(reaction.emoji) == '📊') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📖') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📝') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📔') or \
                   (user == ctx.message.author and str(reaction.emoji) == '❌')
                    # (user == ctx.message.author and str(reaction.emoji) == '🔇') or \

        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            if not isinstance(message.channel, discord.DMChannel):
                await message.clear_reactions()
        else:
            embed = None
            if str(reaction.emoji) == '📊':
                embed = self.pollCommand(ctx)
            if str(reaction.emoji) == '📖':
                embed = self.serverCommand(ctx)
            if str(reaction.emoji) == '📔':
                embed = self.staffCommand(ctx)
            # if str(reaction.emoji) == '🔇':
            #     embed = self.muteCommand(ctx)
            if str(reaction.emoji) == '📝':
                embed = self.serverQuoteCommand(ctx)
            if str(reaction.emoji) == '❌':
                await message.delete()
                if not isinstance(message.channel, discord.DMChannel):
                    await ctx.message.delete()
            if embed is not None:
                await message.edit(embed=embed)
                if not isinstance(message.channel, discord.DMChannel):
                    await reaction.remove(user)
                await self.waitStaffChangeMessage(ctx, message)

    def staffCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Staff commands with clickable categories. You need to be either Owner of the server. Have " \
                      "Administration permissions, or have been added with the addstaff (📖) command. "
        embed.add_field(name='📊', value='Poll')
        embed.add_field(name='📖', value='Server commands')
        embed.add_field(name='📝', value='Server quotes')
        # embed.add_field(name='🔇', value='Mute')
        embed.add_field(name='📔', value='This help message')
        embed.add_field(name='❌', value='Deletes this message')
        embed.set_footer(text='These reactions are available for 60 seconds, afterwards it will stop responding.')
        return embed

    def pollCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Easily added polls for your server."
        embed.add_field(name="poll option 1",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}poll <text>``\nAdds 👍, 👎, 🤷‍ to your text, for questions that don't need specific answers.",
                        inline=False)
        embed.add_field(name="poll option 2",
                        value="``"+self.bot.get_server_prefix(ctx.message)+"poll {title} [answer1] [answer2] ... [answer20]``\nThis command can be used to create a poll with a specific title and specific answers. Note that this command supports up to 20 answers. and the {} around the title and [] around the answers are **required**",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    def serverQuoteCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Your server quotes in the bot."
        embed.add_field(name='global', value=f'``{self.bot.get_server_prefix(ctx.message)}[globalcommand|g] <trigger>``\nReturns your chosen server quote.',
                        inline=False)
        embed.add_field(name='globaladd',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[globaladd|gadd] <trigger> [response]``\nAdds a server quote.',
                        inline=False)
        embed.add_field(name='globalremove',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[globalremove|gremove|grem] <trigger>``\nRemoves a server quote.', inline=False)
        embed.add_field(name='globallist',
                        value=f'``{self.bot.get_server_prefix(ctx.message)}[globallist|glist] [page_number=1]``\nReturns all server quotes.',
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    def serverCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "All commands that can help you customize the your server better."
        embed.add_field(name="addchannel",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}addchannel <channeltypes.TYPE> <channelId>``\nGives a channel a specific type. Check channeltypes which types are available",
                        inline=False)
        embed.add_field(name="addstaff",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}addstaff <roleId>``\nAdds a role to the staff list, this allows users with that specific role to execute the staff commands.",
                        inline=False)
        embed.add_field(name="channeltypes",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}channeltypes``\nTells you which channeltypes there are, and which are available in the addchannel command.",
                        inline=False)
        embed.add_field(name="check",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[check|whois] [member]``\nInformation about a member in your server.",
                        inline=False)
        embed.add_field(name="delchannel",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}delchannel <channelId>``\nRemoves the type from a channel.",
                        inline=False)
        embed.add_field(name="delstaff",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}delstaff <roleId>``\nRemoves a role from the staff list.",
                        inline=False)
        embed.add_field(name="nudge",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}nudge <msgId>``\nMoves a message to the proper channel, with a little warning.",
                        inline=False)
        embed.add_field(name="prefix",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}prefix [prefix]``\nSets the bot's prefix for this server.\nForgot the prefix? Reset it with '@DiscordCrawler#6716 prefix !'.",
                        inline=False)
        embed.add_field(name="purge",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}purge <amount>``\nPurges an x amount of messages, with a little warning.",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed


def setup(bot):
    log.info("[Cog] Help")
    bot.add_cog(Help(bot))
