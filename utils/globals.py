import json

import discord
import motor.motor_asyncio
import time
from discord import VerificationLevel as VL
from discord import VoiceRegion as VR
from discord.ext import commands
import os
from crawler_utilities.handlers.logger import Logger

log = Logger("logs", "CommunityCrawler", "CommunityCrawler").logger

PREFIX = os.environ['PREFIX']
TOKEN = os.environ['TOKEN']
TESTTOKEN = os.environ['TESTTOKEN']
COGS = os.environ['COGS']
COGSECONOMY = os.environ['COGSECONOMY']
COGSADMIN = os.environ['COGSADMIN']
COGSEVENTS = os.environ['COGSEVENTS']
OWNER = int(os.environ['OWNER'])
MONGODB = os.environ['MONGODB']
KEY = os.environ['KEY']

MDB = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['discordCrawler']
HELP = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['lookup']

slashGuilds = [363680385336606740, 584842413135101990, 822493567707775057]

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webp', '.bmp']

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

HONEYPOTCHANNELS = []

def loadChannels(CHANNELDB):
    channel = {}
    for i in CHANNELDB:
        channel[int(i['channel'])] = i['type']
    return channel

def loadHoneypotChannels(HONEYPOTCHANNELSDB):
    channel = {}
    for i in HONEYPOTCHANNELSDB:
        channel[int(i['channelId'])] = i['channelId']
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
        user = ctx.author
        guild = ctx.guild

        if isinstance(user, discord.Member):
            if any(role.id in STAFF for role in user.roles):
                return True
            if user.id in {OWNER, guild.owner_id}:
                return True
            if guild.get_member(user.id).guild_permissions.administrator:
                return True
        else:
            if user.id in {OWNER, guild.owner_id}:
                return True

        return False

    return commands.check(predicate)


def is_staff_bool(ctx):
    user = ctx.author
    guild = ctx.guild

    if isinstance(user, discord.Member):
        if any(role.id in STAFF for role in user.roles):
            return True
        if user.id in {OWNER, guild.owner_id}:
            return True
        if guild.get_member(user.id).guild_permissions.administrator:
            return True
    else:
        if user.id in {OWNER, guild.owner_id}:
            return True

    return False

def is_staff_by_user_bool(user, guild):
    if isinstance(user, discord.Member):
        if any(role.id in STAFF for role in user.roles):
            return True
        if user.id in {OWNER, guild.owner_id}:
            return True
        if guild.get_member(user.id).guild_permissions.administrator:
            return True
    else:
        if user.id in {OWNER, guild.owner_id}:
            return True

    return False


def is_staff_bool_slash(ctx):
    user = ctx.interaction.user
    guild = ctx.guild

    if isinstance(user, discord.Member):
        if any(role.id in STAFF for role in user.roles):
            return True
        if user.id in {OWNER, guild.owner_id}:
            return True
        if guild.get_member(user.id).guild_permissions.administrator:
            return True
    else:
        if user.id in {OWNER, guild.owner_id}:
            return True

    return False

def is_staff_trouble_bool_slash(ctx):
    user = ctx.interaction.user
    guild = ctx.guild

    if isinstance(user, discord.Member):
        if any(r.id in STAFF or r.id == 593720945324326914 for r in user.roles):
            return True
        if user.id in {OWNER, guild.owner_id}:
            return True
        if guild.get_member(user.id).guild_permissions.administrator:
            return True
    else:
        if user.id in {OWNER, guild.owner_id}:
            return True

    return False


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
