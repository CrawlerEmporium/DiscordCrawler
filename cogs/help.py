import asyncio
import typing
import discord
from discord.ext import commands
from utils import globals as GG


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
            await message.add_reaction('🔎')
            await message.add_reaction('👪')
            await message.add_reaction('🎲')
            await message.add_reaction('❓')
            if GG.is_staff_bool(ctx):
                await message.add_reaction('🔒')
            await message.add_reaction('📔')
            await message.add_reaction('❌')

            await self.waitChangeMessage(ctx, message)
        else:
            await ctx.invoke(self.bot.get_command("oldhelp"))
        await GG.upCommand("help")

    async def waitChangeMessage(self, ctx, message):
        def check(reaction, user):
            return (user == ctx.message.author and str(reaction.emoji) == '💬') or \
                   (user == ctx.message.author and str(reaction.emoji) == '💭') or \
                   (user == ctx.message.author and str(reaction.emoji) == '🔎') or \
                   (user == ctx.message.author and str(reaction.emoji) == '👪') or \
                   (user == ctx.message.author and str(reaction.emoji) == '🎲') or \
                   (user == ctx.message.author and str(reaction.emoji) == '❓') or \
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
            if str(reaction.emoji) == '🔎':
                embed = self.lookupCommand(ctx)
            if str(reaction.emoji) == '👪':
                embed = self.charCommand(ctx)
            if str(reaction.emoji) == '🎲':
                embed = self.rollCommand(ctx)
            if str(reaction.emoji) == '❓':
                embed = self.infoCommand(ctx)
            if str(reaction.emoji) == '🔒':
                if GG.is_staff_bool(ctx):
                    embed = self.staffCommand(ctx)
                    await message.clear_reactions()
                    await message.add_reaction('🙊')
                    await message.add_reaction('📊')
                    await message.add_reaction('📖')
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
        embed.add_field(name='🔎', value='Lookup')
        embed.add_field(name='👪', value='Character Options')
        embed.add_field(name='🎲', value='Diceroller')
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

    def infoCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "All information commands."
        embed.add_field(name="botinfo",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[botinfo|stats|info]``\nShows information about <@559331529378103317>", inline=False)
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

    def rollCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "An integrated and extended diceroller."
        embed.add_field(name="iterroll",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[iterroll|rrr] <iterations> <rollStr> [dc=0] [args]``\nRolls dice in xdy format, given a set dc.",
                        inline=False)
        embed.add_field(name="multiroll",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[multiroll|rr] <iterations> <rollStr> [args]``\nRolls dice in xdy format a given number of times.",
                        inline=False)
        embed.add_field(name="roll", value=f"``{self.bot.get_server_prefix(ctx.message)}[roll|r] [rollStr=1d20]``\nRolls dice in xdy format.", inline=False)
        embed.add_field(name="examples",
                        value=f"__Examples__\n{self.bot.get_server_prefix(ctx.message)}roll xdy Attack!\n{self.bot.get_server_prefix(ctx.message)}roll xdy+z adv Attack with Advantage!\n{self.bot.get_server_prefix(ctx.message)}roll xdy-z dis Hide with Heavy Armor!\n{self.bot.get_server_prefix(ctx.message)}roll xdy+xdy*z\n{self.bot.get_server_prefix(ctx.message)}roll XdYkhZ\n{self.bot.get_server_prefix(ctx.message)}roll 4d6mi2[fire] Elemental Adept, Fire\n{self.bot.get_server_prefix(ctx.message)}roll 2d6e6 Explode on 6\n{self.bot.get_server_prefix(ctx.message)}roll 10d6ra6 Spell Bombardment\n{self.bot.get_server_prefix(ctx.message)}roll 4d6ro<3 Great Weapon Master\n__Supported Operators__\nk (keep)\np (drop)\nro (reroll once)\nrr (reroll infinitely)\nmi/ma (min/max result)\ne (explode dice of value)\nra (reroll and add)\n__Supported Selectors_\nlX (lowest X)\nhX (highest X)\n>X/<X (greater than or less than X)",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    def charCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Random character generator options."
        embed.add_field(name="charref",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[charref|makechar] <level> [ua]``\nGives you reference stats for a 5e character. Where ua = 'UA' otherwise it won't let you pick UA options.",
                        inline=False)
        embed.add_field(name="randchar",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}randchar [level=0] [ua]``\nMakes a random 5e character. Where ua = 'UA' otherwise it won't let you pick UA options.",
                        inline=False)
        embed.add_field(name="randname",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}[randname|name] [race] [option]``\nGenerates a random name, optionally from a given race.",
                        inline=False)
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

    def lookupCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Commands to help look up items, status effects, rules, etc."

        embed.add_field(name="background", value=f"``{self.bot.get_server_prefix(ctx.message)}background <name>``\nLooks up a background.", inline=False)
        embed.add_field(name="class",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}class <name> [level]``\nLooks up a class, or all features of a certain level.",
                        inline=False)
        embed.add_field(name="classfeat", value=f"``{self.bot.get_server_prefix(ctx.message)}[classfeat|optionalfeat] <name>``\nLooks up a class feature.",
                        inline=False)
        embed.add_field(name="condition", value=f"``{self.bot.get_server_prefix(ctx.message)}[condition|status] <name>``\nLooks up a condition.", inline=False)
        embed.add_field(name="feat", value=f"``{self.bot.get_server_prefix(ctx.message)}feat <name>``\nLooks up a feat.", inline=False)
        embed.add_field(name="image",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}image <name>``\nShows an image for a monster. May not support all monsters.",
                        inline=False)
        embed.add_field(name="item", value=f"``{self.bot.get_server_prefix(ctx.message)}item <name>``\nLooks up an item.", inline=False)
        embed.add_field(name="monster", value=f"``{self.bot.get_server_prefix(ctx.message)}[monster|creature] <name>``\nLooks up a monster.", inline=False)
        embed.add_field(name="race", value=f"``{self.bot.get_server_prefix(ctx.message)}race <name>``\nLooks up a race.", inline=False)
        embed.add_field(name="racefeat", value=f"``{self.bot.get_server_prefix(ctx.message)}racefeat <name>``\nLooks up a racial feature.", inline=False)
        embed.add_field(name="rule", value=f"``{self.bot.get_server_prefix(ctx.message)}[rule|variantrules] <name>``\nLooks up a rule.", inline=False)
        embed.add_field(name="spell", value=f"``{self.bot.get_server_prefix(ctx.message)}spell <name>``\nLooks up a spell.", inline=False)
        embed.add_field(name="subclass", value=f"``{self.bot.get_server_prefix(ctx.message)}subclass <name>``\nLooks up a subclass.", inline=False)
        embed.add_field(name="token",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}token <name>``\nShows a token for a monster. May not support all monsters.",
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
            await message.add_reaction('🙊')  # Mute
            await message.add_reaction('📊')  # Poll
            await message.add_reaction('📖')  # Server commands
            # Secret command SRD 📜
            await message.add_reaction('📔')
            await message.add_reaction('❌')

            await self.waitStaffChangeMessage(ctx, message)
        else:
            await ctx.invoke(self.bot.get_command("oldhelp"))
        await GG.upCommand("staff")


    async def waitStaffChangeMessage(self, ctx, message):
        def check(reaction, user):
            return (user == ctx.message.author and str(reaction.emoji) == '🙊') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📊') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📖') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📜') or \
                   (user == ctx.message.author and str(reaction.emoji) == '📔') or \
                   (user == ctx.message.author and str(reaction.emoji) == '❌')

        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            if not isinstance(message.channel, discord.DMChannel):
                await message.clear_reactions()
        else:
            embed = None
            if str(reaction.emoji) == '🙊':
                embed = self.muteCommand(ctx)
            if str(reaction.emoji) == '📊':
                embed = self.pollCommand(ctx)
            if str(reaction.emoji) == '📖':
                embed = self.serverCommand(ctx)
            if str(reaction.emoji) == '📜':
                embed = self.srdCommand(ctx)
            if str(reaction.emoji) == '📔':
                embed = self.staffCommand(ctx)
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
        embed.add_field(name='🙊', value='Mute')
        embed.add_field(name='📊', value='Poll')
        embed.add_field(name='📖', value='Server commands')
        embed.add_field(name='📔', value='This help message')
        embed.add_field(name='❌', value='Deletes this message')
        embed.set_footer(text='These reactions are available for 60 seconds, afterwards it will stop responding.')
        return embed

    def muteCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Mute a pesky member for a specified amount of minutes, with X reason."
        embed.add_field(name="mute",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}mute [member] [epoch=10] [reason=No reason given]``\nMutes a member for X minutes. defaults to 10 minutes.",
                        inline=False)
        embed.add_field(name="unmute",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}unmute [member]``\nUnmutes a muted member.",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
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
        embed.add_field(name="prefix",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}prefix [prefix]``\nSets the bot's prefix for this server.\nForgot the prefix? Reset it with '@5eCrawler#2771 prefix !'.",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed

    def srdCommand(self, ctx):
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Non-SRD Content access."
        embed.add_field(name="addsrd",
                        value=f"``{self.bot.get_server_prefix(ctx.message)}addsrd <serverId> <password>``\nGives your server access to all non-SRD material for the lookup commands.\nThe password is found in the support channel for this bot.",
                        inline=False)
        embed.set_footer(
            text='These reactions are available for 60 seconds, afterwards it will stop responding.\n📔 Returns to '
                 'the main menu.\n❌ Deletes this message from chat.')
        return embed


def setup(bot):
    bot.add_cog(Help(bot))
