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


def get_server_prefix(self, msg):
    return self.get_prefix(self, msg)[-1]


def getFlavorText(flavor_text_entries):
    flavor = ""
    for x in range(len(flavor_text_entries)):
        if str(flavor_text_entries[x].language) == "en":
            flavor = flavor_text_entries[x].flavor_text
            break
    return flavor.replace("\n"," ")

def getDescriptionText(descriptions):
    description = ""
    for x in range(len(descriptions)):
        if str(descriptions[x].language) == "en":
            description = descriptions[x].description
            break
    return description.replace("\n"," ")

def getEffectText(effect_entries):
    effect = ""
    for x in range(len(effect_entries)):
        if str(effect_entries[x].language) == "en":
            effect = effect_entries[x].effect
            break
    return effect

def getNames(names):
    name = ""
    for x in range(len(names)):
        if str(names[x].language) == "en":
            name = names[x].name
            break
    return name.replace("\n"," ")

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


def getColorOfType(type):
    if type == "normal": return "a8a878"
    if type == "fighting": return "c03028"
    if type == "flying": return "a890f0"
    if type == "poison": return "a040a0"
    if type == "ground": return "e0c068"
    if type == "rock": return "b8a038"
    if type == "bug": return "a8b820"
    if type == "ghost": return "705898"
    if type == "steel": return "b8b8d0"
    if type == "fire": return "f08030"
    if type == "water": return "6890f0"
    if type == "grass": return "78c850"
    if type == "electric": return "f8d030"
    if type == "psychic": return "f85888"
    if type == "ice": return "98d8d8"
    if type == "dragon": return "7038f8"
    if type == "dark": return "705848"
    if type == "fairy": return "faadff"


def cleanWordDash(insert):
    out = insert.replace("-"," ")
    out = string.capwords(out)
    return out


def cleanWordSpace(insert):
    out = insert.replace(" ","-").lower()
    return out


class EmbedWithAuthor(discord.Embed):
    """An embed with author image and nickname set."""

    def __init__(self, ctx, **kwargs):
        super(EmbedWithAuthor, self).__init__(**kwargs)
        self.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        self.colour = random.randint(0, 0xffffff)


def getGame(name):
    if name == "red-blue":
        return "Red / Blue"
    if name == "yellow":
        return "Yellow"
    if name == "gold-silver":
        return "Gold / Silver"
    if name == "crystal":
        return "Crystal"
    if name == "ruby-sapphire":
        return "Ruby / Sapphire"
    if name == "emerald":
        return "Emerald"
    if name == "firered-leafgrean":
        return "Fire Red / Leaf Green"
    if name == "diamond-pearl":
        return "Diamond / Pearl"
    if name == "platinum":
        return "Platinum"
    if name == "heartgold-soulsilver":
        return "Heart Gold / Soul Silver"
    if name == "black-white":
        return "Black / White"
    if name == "colosseum":
        return "Colosseum"
    if name == "xd":
        return "XD"
    if name == "black-2-white-2":
        return "Black 2 / White 2"
    if name == "x-y":
        return "X / Y"
    if name == "omega-ruby-alpha-sapphire":
        return "Omega Ruby / Alpha Sapphire"
    if name == "sun-moon":
        return "Sun / Moon"
    if name == "ultra-sun-ultra-moon":
        return "Ultra Sun / Ultra Moon"

TYPES = ['normal', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost', 'steel', 'fire', 'water', 'grass', 'electric', 'psychic', 'ice', 'dragon', 'dark', 'fairy']