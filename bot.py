import asyncio
import json
from os import listdir
from os.path import isfile, join

import discord

import utils.globals as GG
from discord.ext import commands

from crawler_utilities.handlers import logger
from models.buttons.greylist import Greylist

log = logger.logger

version = "v2.6.0"
SHARD_COUNT = 1
TESTING = False
defaultPrefix = GG.PREFIX if not TESTING else '*'
COGS = [GG.COGS, GG.COGSADMIN, GG.COGSECONOMY, "cogsToBeDetermined"]
intents = discord.Intents().default()
intents.members = True
intents.message_content = True


async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or(defaultPrefix)(bot, message)
    guild_id = str(message.guild.id)
    if guild_id in bot.prefixes:
        gp = bot.prefixes.get(guild_id, defaultPrefix)
    else:  # load from db and cache
        gp_obj = await GG.MDB.prefixes.find_one({"guild_id": guild_id})
        if gp_obj is None:
            gp = defaultPrefix
        else:
            gp = gp_obj.get("prefix", defaultPrefix)
        bot.prefixes[guild_id] = gp
    return commands.when_mentioned_or(gp)(bot, message)


class Crawler(commands.AutoShardedBot):
    def __init__(self, prefix, help_command=None, **options):
        super(Crawler, self).__init__(prefix, help_command, **options)
        self.version = version
        self.owner = None
        self.testing = TESTING
        if self.testing:
            self.token = GG.TESTTOKEN
        else:
            self.token = GG.TOKEN
        self.mdb = GG.MDB
        self.prefixes = dict()
        self.guild = None
        self.tracking = 737222675293929584
        self.error = 858336420418813963
        self.defaultPrefix = GG.PREFIX
        self.port = 5000

    async def get_server_prefix(self, msg):
        return (await get_prefix(self, msg))[-1]

    async def launch_shards(self):
        if self.shard_count is None:
            recommended_shards, _ = await self.http.get_bot_gateway()
            if recommended_shards >= 96 and not recommended_shards % 16:
                # half, round up to nearest 16
                self.shard_count = recommended_shards // 2 + (16 - (recommended_shards // 2) % 16)
            else:
                self.shard_count = recommended_shards // 2
        log.info(f"Launching {self.shard_count} shards!")
        await super(Crawler, self).launch_shards()


bot = Crawler(prefix=get_prefix, intents=intents, case_insensitive=True, status=discord.Status.idle,
              shard_count=SHARD_COUNT, testing=TESTING,
              activity=discord.Game(f"$help | Initializing..."))


@bot.event
async def on_message(msg):
    if msg.author.id == 645958319982510110 or not msg.author.bot:
        await bot.invoke(await bot.get_context(msg))


@bot.event
async def on_ready():
    loadButtons(bot)
    await bot.change_presence(activity=discord.Game(f"with {len(bot.guilds)} servers | $help | {version}"))
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


@bot.event
async def on_thread_join(thread):
    await thread.join()


@bot.event
async def on_connect():
    await fillGlobals()
    await bot.sync_commands(force=True)
    bot.owner = await bot.fetch_user(GG.OWNER)
    print(f"OWNER: {bot.owner.name}")


@bot.event
async def on_resumed():
    log.info('resumed.')


async def fillGlobals():
    log.info("Filling Globals")
    CHANNELDB = await GG.MDB['channelinfo'].find({}).to_list(length=None)
    GG.CHANNEL = GG.loadChannels(CHANNELDB)

    REPORTERSDB = await GG.MDB['reports'].find({}).to_list(length=None)
    GG.REPORTERS = [int(i['message']) for i in REPORTERSDB]

    STAFFDB = await GG.MDB['serverstaff'].find({}).to_list(length=None)
    GG.STAFF = [int(i['roles']) for i in STAFFDB]

    TERMDB = await GG.MDB['blacklist'].find({}).to_list(length=None)
    GG.TERMS = [int(i['guild']) for i in TERMDB]

    GREYDB = await GG.MDB['greylist'].find({}).to_list(length=None)
    GG.GREYS = [int(i['guild']) for i in GREYDB]

    REACTIONROLESDB = await GG.MDB['reactionroles'].find({}).to_list(length=None)
    GG.REACTIONROLES = GG.loadReactionRoles(REACTIONROLESDB)

    GG.BLACKLIST, GG.GUILDS = await GG.fillBlackList(GG.BLACKLIST, GG.GUILDS)
    GG.GREYLIST, GG.GREYGUILDS = await GG.fillGreyList(GG.GREYLIST, GG.GREYGUILDS)
    log.info("Finished Filling Globals")


def loadCogs():
    i = 0
    for COG in COGS:
        log.info(f"Loading {COG}...")
        for extension in [f.replace('.py', '') for f in listdir(GG.COG) if isfile(join(GG.COG, f))]:
            try:
                bot.load_extension(COG + "." + extension)
            except Exception as e:
                print(e)
                log.error(f'Failed to load extension {extension}')
                i += 1
        log.info("-------------------")

    if i == 0:
        log.info("Finished Loading All Cogs...")
    else:
        log.info(f"Finished Loading Cogs with {i} errors...")


def loadCrawlerUtilitiesCogs():
    cu_event_extensions = ["errors", "joinLeave"]
    cu_event_folder = "crawler_utilities.events"
    cu_cogs_extensions = ["flare", "stats", "help", "localization"]
    cu_cogs_folder = "crawler_utilities.cogs"

    i = 0
    log.info("Loading Cogs...")
    for extension in cu_cogs_extensions:
        try:
            bot.load_extension(f"{cu_cogs_folder}.{extension}")
        except Exception as e:
            print(e)
            log.error(f'Failed to load extension {extension}')
            i += 1
    log.info("-------------------")
    log.info("Loading Event Cogs...")
    for extension in cu_event_extensions:
        try:
            bot.load_extension(f"{cu_event_folder}.{extension}")
        except Exception as e:
            log.error(f'Failed to load extension {extension}')
            i += 1
    log.info("-------------------")
    if i == 0:
        log.info("Finished Loading All Utility Cogs...")
    else:
        log.info(f"Finished Loading Utility Cogs with {i} errors...")


def loadButtons(bot):
    bot.add_view(Greylist(bot))


if __name__ == "__main__":
    bot.state = "run"
    loadCrawlerUtilitiesCogs()
    loadCogs()
    bot.run(bot.token)
