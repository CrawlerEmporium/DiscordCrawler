import asyncio
import datetime

import discord
import time

from discord import VerificationLevel as VL, ButtonStyle
from discord import VoiceRegion as VR

from discord.ext.commands import BucketType
from discord.ui import Button

from discord.ext import commands
from utils import globals as GG
from crawler_utilities.utils.embeds import EmbedWithRandomColor
from crawler_utilities.utils.functions import fakeField, countChannels

log = GG.log

VERIFLEVELS = {VL.none: "None", VL.low: "Low", VL.medium: "Medium", VL.high: "(╯°□°）╯︵  ┻━┻"}
REGION = {VR.brazil: ":flag_br: Brazil",
          VR.eu_central: ":flag_eu: Central Europe",
          VR.singapore: ":flag_sg: Singapore",
          VR.us_central: ":flag_us: U.S. Central",
          VR.sydney: ":flag_au: Sydney",
          VR.us_east: ":flag_us: U.S. East",
          VR.us_south: ":flag_us: U.S. South",
          VR.us_west: ":flag_us: U.S. West",
          VR.eu_west: ":flag_eu: Western Europe",
          VR.vip_us_east: ":flag_us: VIP U.S. East",
          VR.vip_us_west: ":flag_us: VIP U.S. West",
          VR.vip_amsterdam: ":flag_nl: VIP Amsterdam",
          VR.london: ":flag_gb: London",
          VR.amsterdam: ":flag_nl: Amsterdam",
          VR.frankfurt: ":flag_de: Frankfurt",
          VR.hongkong: ":flag_hk: Hong Kong",
          VR.russia: ":flag_ru: Russia",
          VR.japan: ":flag_jp: Japan",
          VR.southafrica: ":flag_za:  South Africa"}


def checkDays(date):
    now = date.fromtimestamp(time.time())
    diff = now - date
    days = diff.days
    return f"{days} {'day' if days == 1 else 'days'} ago"


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.monotonic()

    @commands.command()
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Shows info about server"""
        await ctx.guild.chunk()
        HUMANS = ctx.guild.members
        BOTS = []
        for h in HUMANS:
            if h.bot is True:
                BOTS.append(h)
                HUMANS.remove(h)
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.add_field(name="Name", value=ctx.guild.name)
        embed.add_field(name="Owner", value=ctx.guild.owner)
        fakeField(embed)
        embed.add_field(name="Verification Level", value=VERIFLEVELS[ctx.guild.verification_level])
        embed.add_field(name="Total | Humans | Bots", value=f"{len(ctx.guild.members)} | {len(HUMANS)} | {len(BOTS)}")
        text, voice = countChannels(ctx.guild.channels)
        fakeField(embed)
        embed.add_field(name="Text Channels", value=str(text))
        embed.add_field(name="Voice Channels", value=str(voice))
        fakeField(embed)
        time = str(ctx.guild.created_at.timestamp()).split(".")
        embed.add_field(name="Creation Date", value=f"{ctx.guild.created_at}\n<t:{time[0]}:R>", inline=False)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    @commands.command(aliases=['stats', 'info'])
    async def botinfo(self, ctx):
        """Shows info about bot"""
        em = discord.Embed(color=discord.Color.green(),
                           description="DiscordCrawler, a bot for moderation and other helpful things.")
        em.title = 'Bot Info'
        em.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        em.add_field(name="Servers", value=str(len(ctx.bot.guilds)))
        total_members = sum(len(s.members) for s in self.bot.guilds)
        unique_members = set(self.bot.get_all_members())
        members = '%s total\n%s unique' % (total_members, len(unique_members))
        em.add_field(name='Members', value=members)
        em.add_field(name='Uptime', value=str(datetime.timedelta(seconds=round(time.monotonic() - self.start_time))))
        totalText = 0
        totalVoice = 0
        for g in ctx.bot.guilds:
            text, voice = GG.countChannels(g.channels)
            totalText += text
            totalVoice += voice
        em.add_field(name='Text Channels', value=f"{totalText}")
        em.add_field(name='Voice Channels', value=f"{totalVoice}")
        em.add_field(name="Invite",
                     value="[Click Here](https://discord.com/api/oauth2/authorize?client_id=602774912595263490&permissions=805412928&scope=bot%20applications.commands)")
        em.add_field(name='Source', value="[Click Here](https://github.com/CrawlerEmporium/DiscordCrawler)")
        em.add_field(name='Issue Tracker',
                     value="[Click Here](https://github.com/CrawlerEmporium/DiscordCrawler/issues)")
        em.add_field(name="About",
                     value='A multipurpose bot made by LordDusk#0001 .\n[Support Server](https://discord.gg/HEY6BWj)')
        em.set_footer(text=f"DiscordCrawler {ctx.bot.version} | Powered by discord.py")
        await ctx.send(embed=em)

    @commands.command()
    async def support(self, ctx):
        em = EmbedWithRandomColor()
        em.title = 'Support Server'
        em.description = "For technical support for DiscordCrawler, join the Crawler Emporium discord [here](https://discord.gg/HEY6BWj)!\n" \
                         "There you can ask questions about the bot, make feature requests, report issues and/or bugs (please include any error messages), learn about my other Crawler bots, and share with other crawler bot users!\n\n" \
                         "[Check the Website](https://crawleremporium.com) for even more information.\n\n" \
                         "To add premium features to the bot, [<:Patreon:855754853153505280> Join the Patreon](https://www.patreon.com/LordDusk), or if you'd rather show just appreciation [tip the Developer a <:Kofi:855758703772958751> here](https://ko-fi.com/5ecrawler)."
        serverEmoji = self.bot.get_emoji(int("<:5e:603932658820448267>".split(":")[2].replace(">", "")))
        patreonEmoji = self.bot.get_emoji(int("<:Patreon:855754853153505280>".split(":")[2].replace(">", "")))
        kofiEmoji = self.bot.get_emoji(int("<:Kofi:855758703772958751>".split(":")[2].replace(">", "")))
        view = discord.ui.View()
        view.add_item(Button(label="Discord", style=ButtonStyle.url, emoji=serverEmoji, url="https://discord.gg/HEY6BWj"))
        view.add_item(Button(label="Website", style=ButtonStyle.url, url="https://www.crawleremporium.com"))
        view.add_item(Button(label="Patreon", style=ButtonStyle.url, emoji=patreonEmoji, url="https://www.patreon.com/LordDusk"))
        view.add_item(Button(label="Buy me a coffee", style=ButtonStyle.url, emoji=kofiEmoji, url="https://ko-fi.com/5ecrawler"))
        await ctx.send(embed=em, view=view)

    @commands.command()
    async def invite(self, ctx):
        em = EmbedWithRandomColor()
        em.title = 'Invite Me!'
        em.description = "Hi, you can easily invite me to your own server by following [this link](" \
                         "https://discord.com/api/oauth2/authorize?client_id=602774912595263490&permissions=805412928&scope=bot%20applications.commands" \
                         "=805412928)!\n\nOf the 5 permissions asked, 4 are optional and 1 mandatory for optimal " \
                         "usage of the capabilities of the bot.\n\n**Mandatory:**\n__Manage Messages__ - this allows the " \
                         "bot to remove messages from other users.\n\n**Optional:**\n__Manage Webhooks__ - There are 2 " \
                         "ways for the quote command to function. One where it will use a webhook to give a reply as " \
                         "the person who quoted the message. Or one where it will just reply in text, but as the bot.\n\n" \
                         "__Attach Files__ - Some commands or replies will let the bot attach images/files, " \
                         "without this permission it will not be able too.\n\n" \
                         "__Add Reactions__ - For the Anon/Delivery the bot requires to be able to add reactions to " \
                         "messages that are send.\n\n" \
                         "__Manage Roles__ - For the Reaction Roles, the bot needs to be able to give users a role.\n\n" \
                         "__Read History__ - For some things to work (edit message, add reactions) the bot requires " \
                         "to be able to read the history of the channel. If it lacks this permission, but does have. " \
                         "Add Reactions, it will pelt you with 'Permission not found.'"
        view = discord.ui.View()
        serverEmoji = self.bot.get_emoji(int("<:DiscordCrawler:855754497321074709>".split(":")[2].replace(">", "")))
        view.add_item(Button(label="Invite me!", style=ButtonStyle.url, emoji=serverEmoji, url="https://discord.com/api/oauth2/authorize?client_id=602774912595263490&permissions=805412928&scope=bot%20applications.commands"))
        await ctx.send(embed=em, view=view)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def emojis(self, ctx):
        string = ""
        for x in ctx.guild.emojis:
            string += f"{x} -- ``{x}``\n"
            if (len(string) > 900):
                await ctx.send(string)
                string = ""
        await ctx.send(string)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def ten(self, ctx):
        guild = ctx.guild
        await guild.chunk()
        members = sorted(guild.members, key=lambda m: m.joined_at)
        users = ""
        for i in range(20):
            users += f"#{i+1} - {members[i].mention}\n"
        await ctx.send(users)

    @commands.command(hidden=True)
    @commands.cooldown(1, 60, BucketType.user)
    @commands.max_concurrency(1, BucketType.user)
    async def multiline(self, ctx, *, cmds: str):
        """Runs each line as a separate command, with a 1 second delay between commands.
        Limited to 1 multiline every 60 seconds, with a max of 10 commands, due to abuse.
        Usage:
        "!multiline
        !command1
        !command2
        !command3"
        """
        cmds = cmds.splitlines()
        for c in cmds[:10]:
            ctx.message.content = c
            await self.bot.process_commands(ctx.message)
            await asyncio.sleep(1)

def setup(bot):
    log.info("[Cog] Info")
    bot.add_cog(Info(bot))
