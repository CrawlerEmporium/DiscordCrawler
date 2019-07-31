import random
import string
import time

import discord
from discord.ext import commands
from environs import Env
from discord import VerificationLevel as VL
from discord import VoiceRegion as VR

from DBService import DBService

env = Env()
env.read_env()

PREFIX = env('PREFIX')
TOKEN = env('TOKEN')
COGS = env('COGS')
OWNER = int(env('OWNER'))

BOT = 574554734187380756
PM_TRUE = True
PREFIXESDB = DBService.exec("SELECT Guild, Prefix FROM Prefixes").fetchall()


def loadChannels(PREFIXESDB):
    prefixes = {}
    for i in PREFIXESDB:
        prefixes[str(i[0])] = str(i[1])
    return prefixes


PREFIXES = loadChannels(PREFIXESDB)

TERMDB = DBService.exec("SELECT Guild FROM Terms").fetchall()
TERMS = [int(i[0]) for i in TERMDB]
GREYDB = DBService.exec("SELECT Guild FROM Grey").fetchall()
GREYS = [int(i[0]) for i in GREYDB]
CLEANER = [496672117384019969,280892074247716864]

def is_owner():
    async def predicate(ctx):
        if ctx.author.id == OWNER or ctx.author.id == ctx.guild.owner_id:
            return True
        else:
            return False

    return commands.check(predicate)


def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(predicate)

def is_cleaner():
    async def predicate(ctx):
        if isinstance(ctx.author, discord.Member):
            if ctx.author.roles is not None:
                for r in ctx.author.roles:
                    if r.id in CLEANER:
                        return True
                return False
            return False
        return False
    return commands.check(predicate)

def get_server_prefix(self, msg):
    return self.get_prefix(self, msg)[-1]

def countChannels(channels):
    channelCount = 0
    voiceCount = 0
    for x in channels:
        if type(x) is discord.TextChannel:
            channelCount += 1
        elif type(x) is discord.VoiceChannel:
            voiceCount += 1
        else:
            pass
    return channelCount, voiceCount

VERIFLEVELS = {VL.none: "None", VL.low: "Low", VL.medium: "Medium", VL.high: "(╯°□°）╯︵  ┻━┻",
               VL.extreme: "┻━┻ミヽ(ಠ益ಠ)ノ彡┻━┻"}
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


class EmbedWithAuthor(discord.Embed):
    """An embed with author image and nickname set."""

    def __init__(self, ctx, **kwargs):
        super(EmbedWithAuthor, self).__init__(**kwargs)
        self.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        self.colour = random.randint(0, 0xffffff)