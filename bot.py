import asyncio
import discord
import utils.globals as GG

from utils import logger
from os import listdir
from os.path import isfile, join
from discord.ext import commands

log = logger.logger

version = "v2.0.2"
SHARD_COUNT = 1
TESTING = False
defaultPrefix = GG.PREFIX if not TESTING else '*'
intents = discord.Intents().all()


def get_prefix(b, message):
    if not message.guild:
        return commands.when_mentioned_or(defaultPrefix)(b, message)

    gp = b.prefixes.get(str(message.guild.id), defaultPrefix)
    return commands.when_mentioned_or(gp)(b, message)


class Crawler(commands.AutoShardedBot):
    def __init__(self, prefix, help_command=None, description=None, **options):
        super(Crawler, self).__init__(prefix, help_command, description, **options)
        self.version = version
        self.owner = None
        self.testing = TESTING
        self.token = GG.TOKEN
        self.mdb = GG.MDB
        self.prefixes = GG.PREFIXES

    def get_server_prefix(self, msg):
        return get_prefix(self, msg)[-1]

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
              description="A bot.", shard_count=SHARD_COUNT, testing=TESTING,
              activity=discord.Game(f"$help | {version}"),
              help_command=commands.DefaultHelpCommand(command_attrs={"name": "oldhelp"}))


@bot.event
async def on_message(msg):
    if msg.author.id == 645958319982510110 or not msg.author.bot:
        await bot.invoke(await bot.get_context(msg))


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(f"with {len(bot.guilds)} servers | $help | {version}"), afk=True)
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


@bot.event
async def on_connect():
    await fillGlobals()
    bot.owner = await bot.fetch_user(GG.OWNER)
    print(f"OWNER: {bot.owner.name}")


@bot.event
async def on_resumed():
    log.info('resumed.')


async def fillGlobals():
    log.info("Filling Globals")
    PREFIXESDB = await GG.MDB['prefixes'].find({}).to_list(length=None)
    GG.PREFIXES = GG.loadPrefixes(PREFIXESDB)
    bot.prefixes = GG.PREFIXES

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


if __name__ == "__main__":
    bot.state = "run"
    for extension in [f.replace('.py', '') for f in listdir(GG.COGS) if isfile(join(GG.COGS, f))]:
        try:
            bot.load_extension(GG.COGS + "." + extension)
        except Exception as e:
            log.error(f'Failed to load extension {extension}')
    for extension in [f.replace('.py', '') for f in listdir(GG.COGSECONOMY) if isfile(join(GG.COGSECONOMY, f))]:
        try:
            bot.load_extension(GG.COGSECONOMY + "." + extension)
        except Exception as e:
            log.error(f'Failed to load extension {extension}')
    for extension in [f.replace('.py', '') for f in listdir(GG.COGSADMIN) if isfile(join(GG.COGSADMIN, f))]:
        try:
            bot.load_extension(GG.COGSADMIN + "." + extension)
        except Exception as e:
            log.error(f'Failed to load extension {extension}')
    for extension in [f.replace('.py', '') for f in listdir(GG.COGSEVENTS) if isfile(join(GG.COGSEVENTS, f))]:
        try:
            bot.load_extension(GG.COGSEVENTS + "." + extension)
        except Exception as e:
            log.error(f'Failed to load extension {extension}')
    bot.run(bot.token)
