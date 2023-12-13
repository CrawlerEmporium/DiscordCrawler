import json

import discord
import motor.motor_asyncio
import time
from discord import VerificationLevel as VL
from discord import VoiceRegion as VR
from discord.ext import commands
from environs import Env
from crawler_utilities.handlers.logger import Logger

log = Logger("logs", "CommunityCrawler", "CommunityCrawler").logger

env = Env()
env.read_env()

PREFIX = env('PREFIX')
TOKEN = env('TOKEN')
TESTTOKEN = env('TESTTOKEN')
COGS = env('COGS')
COGSECONOMY = env('COGSECONOMY')
COGSADMIN = env('COGSADMIN')
COGSEVENTS = env('COGSEVENTS')
OWNER = int(env('OWNER'))
MONGODB = env('MONGODB')
KEY = env('KEY')

MDB = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['discordCrawler']
HELP = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['lookup']

slashGuilds = [363680385336606740, 584842413135101990, 822493567707775057]

BOT = 574554734187380756
PM_TRUE = True

CHANNEL = []
REPORTERS = []
STAFF = []
TERMS = []
GREYS = []
REACTIONROLES = []

BLACKLIST = ""
GREYLIST = ""
GUILDS = []
GREYGUILDS = []

def loadChannels(CHANNELDB):
    channel = {}
    for i in CHANNELDB:
        channel[int(i['channel'])] = i['type']
    return channel


def loadPrefixes(PREFIXESDB):
    prefixes = {}
    for i in PREFIXESDB:
        prefixes[str(i['guild'])] = str(i['prefix'])
    return prefixes


def loadReactionRoles(REACTIONROLESDB):
    reactionRole = {}
    for i in REACTIONROLESDB:
        key = int(i['messageId'])
        if key not in reactionRole:
            reactionRole[key] = []
        reactionRole[key].append((i['roleId'], i['emoji']))
    return reactionRole


async def fillBlackList(BLACKLIST, GUILDS):
    BLACKLIST = "["
    TERMDB = await MDB['blacklist'].find({}).to_list(length=None)
    guildList = []
    for x in TERMDB:
        if x['guild'] not in guildList:
            guildList.append(x['guild'])
    for y in guildList:
        guildTermList = []
        for x in TERMDB:
            if y == x['guild']:
                guildTermList.append(x['term'])
        termList = ""
        for x in guildTermList:
            termList += f'"{x}",'
        termList = termList[:-1]
        guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
        BLACKLIST += guildTerms
    BLACKLIST = BLACKLIST[:-1]
    BLACKLIST += "]"
    BLACKLIST = json.loads(BLACKLIST)
    for x in BLACKLIST:
        GUILDS.append(x['guild'])
    return BLACKLIST, GUILDS


async def fillGreyList(GREYLIST, GREYGUILDS):
    GREYLIST = "["
    TERMDB = await MDB['greylist'].find({}).to_list(length=None)
    guildList = []
    for x in TERMDB:
        if x['guild'] not in guildList:
            guildList.append(x['guild'])
    for y in guildList:
        guildTermList = []
        for x in TERMDB:
            if y == x['guild']:
                guildTermList.append(x['term'])
        termList = ""
        for x in guildTermList:
            termList += f'"{x}",'
        termList = termList[:-1]
        guildTerms = '{"guild":' + str(y) + ',"terms":[' + termList + ']},'
        GREYLIST += guildTerms
    GREYLIST = GREYLIST[:-1]
    GREYLIST += "]"
    GREYLIST = json.loads(GREYLIST)
    for x in GREYLIST:
        GREYGUILDS.append(x['guild'])
    return GREYLIST, GREYGUILDS


CLEANER = [496672117384019969, 280892074247716864]


def checkPermission(ctx, permission):
    if ctx.guild is None:
        return True
    if permission == "mm":
        return ctx.guild.me.guild_permissions.manage_messages
    if permission == "mw":
        return ctx.guild.me.guild_permissions.manage_webhooks
    if permission == "af":
        return ctx.guild.me.guild_permissions.attach_files
    if permission == "ar":
        return ctx.guild.me.guild_permissions.add_reactions
    else:
        return False


def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(predicate)


def is_staff():
    async def predicate(ctx):
        global allowed
        if isinstance(ctx.author, discord.Member):
            if ctx.author.roles is not None:
                for r in ctx.author.roles:
                    if r.id in STAFF:
                        allowed = True
                        break
                    else:
                        allowed = False

                if ctx.author.id == OWNER or ctx.author.id == ctx.guild.owner_id:
                    allowed = True
            else:
                allowed = False
        else:
            try:
                if ctx.author.id == OWNER or ctx.author.id == ctx.guild.owner_id:
                    allowed = True
                else:
                    allowed = False
            except Exception:
                allowed = False

        try:
            if ctx.guild.get_member(ctx.author.id).guild_permissions.administrator:
                allowed = True
        except:
            pass

        return allowed

    return commands.check(predicate)


def is_staff_bool(ctx):
    global allowed
    if isinstance(ctx.author, discord.Member):
        if ctx.author.roles is not None:
            for r in ctx.author.roles:
                if r.id in STAFF:
                    allowed = True
                    break
                else:
                    allowed = False

            if ctx.author.id == OWNER or ctx.author.id == ctx.guild.owner_id:
                allowed = True
        else:
            allowed = False
    else:
        try:
            if ctx.author.id == OWNER or ctx.author.id == ctx.guild.owner_id:
                allowed = True
            else:
                allowed = False
        except Exception:
            allowed = False

    try:
        if ctx.guild.get_member(ctx.author.id).guild_permissions.administrator:
            allowed = True
    except:
        pass

    return allowed


def is_staff_bool_slash(ctx):
    global allowed
    if isinstance(ctx.interaction.user, discord.Member):
        if ctx.interaction.user.roles is not None:
            for r in ctx.interaction.user.roles:
                if r.id in STAFF:
                    allowed = True
                    break
                else:
                    allowed = False

            if ctx.interaction.user.id == OWNER or ctx.interaction.user.id == ctx.guild.owner_id:
                allowed = True
        else:
            allowed = False
    else:
        try:
            if ctx.interaction.user.id == OWNER or ctx.interaction.user.id == ctx.guild.owner_id:
                allowed = True
            else:
                allowed = False
        except Exception:
            allowed = False

    try:
        if ctx.guild.get_member(ctx.interaction.user.id).guild_permissions.administrator:
            allowed = True
    except:
        pass

    return allowed


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


def cutStringInPieces(input):
    n = 900
    output = [input[i:i + n] for i in range(0, len(input), n)]
    return output


def cutListInPieces(input):
    n = 30
    output = [input[i:i + n] for i in range(0, len(input), n)]
    return output


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


def get_server_prefix(self, msg):
    return self.get_prefix(self, msg)[-1]

def get_status(boolean):
    if boolean:
        return "Open"
    return "Closed"

def human_readable_boolean(boolean):
    if boolean:
        return "Yes"
    return "No"

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


async def reloadReactionRoles():
    REACTIONROLESDB = await MDB['reactionroles'].find({}).to_list(length=None)
    return loadReactionRoles(REACTIONROLESDB)

def id_to_snowflake(_id):
    return str(((_id >> 22) + 1420070400000) / 1000).split('.')[0]
