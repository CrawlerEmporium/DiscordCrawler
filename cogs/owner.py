import asyncio
import os
import subprocess
import inspect

import discord

import utils.globals as GG
from discord.ext import commands

from utils import logger

log = logger.logger

extensions = [x.replace('.py', '') for x in os.listdir(GG.COGS) if x.endswith('.py')]
path = GG.COGS + '.'


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def gitpull(self, ctx):
        """Pulls from github and updates bot"""
        await ctx.trigger_typing()
        await ctx.send(f"```{subprocess.run('git pull', stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')}```")
        for cog in extensions:
            ctx.bot.unload_extension(f'{path}{cog}')
        for cog in extensions:
            members = inspect.getmembers(cog)
            for name, member in members:
                if name.startswith('on_'):
                    ctx.bot.add_listener(member, name)
            try:
                ctx.bot.load_extension(f'{path}{cog}')
            except Exception as e:
                await ctx.send(f'LoadError: {cog}\n{type(e).__name__}: {e}')
        await ctx.send('All cogs reloaded :white_check_mark:')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def presenceLite(self, ctx):
        msqQueue = []
        msg = '```js\n'
        msg += '{!s:19s} | {!s:>8s} | {} | {}\n'.format('ID', 'Member', 'Name', 'Owner')
        for guild in self.bot.guilds:
            msg += '{!s:19s} | {!s:>8s}| {} | {}\n'.format(guild.id, guild.member_count, guild.name, guild.owner)
            if len(msg) > 900:
                msg += '```'
                msqQueue.append(msg)
                msg = '```js\n'
                msg += '{!s:19s} | {!s:>8s} | {} | {}\n'.format('ID', 'Member', 'Name', 'Owner')
        msg += '```'
        if len(msqQueue) > 0:
            for x in msqQueue:
                await ctx.send(x)
        else:
            await ctx.send(msg)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension_name: str):
        """[OWNER ONLY]"""
        if ctx.author.id == GG.OWNER:
            try:
                ctx.bot.load_extension(GG.COGS + "." + extension_name)
            except (AttributeError, ImportError) as e:
                await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
                return
            await ctx.send("{} loaded".format(extension_name))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, extension_name: str):
        """[OWNER ONLY]"""
        if ctx.author.id == GG.OWNER:
            ctx.bot.unload_extension(GG.COGS + "." + extension_name)
            await ctx.send("{} unloaded".format(extension_name))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def botcheck(self, ctx):
        await ctx.send(f"Checking {len(ctx.bot.guilds)} servers for bot collection servers.")
        for guild in ctx.bot.guilds:
            bots = sum(1 for m in guild.members if m.bot)
            members = len(guild.members)
            ratio = bots / members
            if ratio >= 0.6 and members >= 20:
                log.info("Detected bot collection server ({}), ratio {}. Leaving.".format(guild.id, ratio))
                try:
                    await guild.owner.send("Please do not add me to bot collection servers. "
                                           "Your server was flagged for having over 60% bots. "
                                           "If you believe this is an error, please PM the bot author.")
                except:
                    pass
                await asyncio.sleep(members / 200)
                await guild.leave()
        await ctx.bot.change_presence(
            activity=discord.Game(f"with {len(ctx.bot.guilds)} servers | !help | {ctx.bot.version}"), afk=True)


def setup(bot):
    log.info("[Cog] Owner")
    bot.add_cog(Owner(bot))
