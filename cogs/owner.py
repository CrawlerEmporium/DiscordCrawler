import asyncio
import os
import subprocess
import inspect

import discord
from discord import permissions, slash_command

import utils.globals as GG
from discord.ext import commands

from crawler_utilities.handlers import logger

log = logger.logger

extensions = [x.replace('.py', '') for x in os.listdir(GG.COGS) if x.endswith('.py')]
extensionsAdmin = [x.replace('.py', '') for x in os.listdir(GG.COGSADMIN) if x.endswith('.py')]
extensionsEconomy = [x.replace('.py', '') for x in os.listdir(GG.COGSECONOMY) if x.endswith('.py')]
extensionsDetermined = [x.replace('.py', '') for x in os.listdir("cogsToBeDetermined") if x.endswith('.py')]

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="gitpull", guild_ids=[584842413135101990])
    async def gitpull(self, ctx):
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        """Pulls from github and updates bot"""
        subprocess.run('git pull', stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
        await self.reloadCogs(ctx)

    @slash_command(name="reloadcogs", guild_ids=[584842413135101990])
    async def reloadCogs(self, ctx):
        """Reloads all cogs from the bot"""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await self.reload(ctx)

    async def reload(self, ctx):
        errorString = ""
        for cog in extensions:
            ctx.bot.unload_extension(f'{GG.COGS}.{cog}')
        for cog in extensions:
            members = inspect.getmembers(cog)
            for name, member in members:
                if name.startswith('on_'):
                    ctx.bot.add_listener(member, name)
            try:
                ctx.bot.load_extension(f'{GG.COGS}.{cog}')
            except:
                errorString += "Error found in cogs\n"
        for cog in extensionsAdmin:
            ctx.bot.unload_extension(f'{GG.COGSADMIN}.{cog}')
        for cog in extensionsAdmin:
            members = inspect.getmembers(cog)
            for name, member in members:
                if name.startswith('on_'):
                    ctx.bot.add_listener(member, name)
            try:
                ctx.bot.load_extension(f'{GG.COGSADMIN}.{cog}')
            except:
                errorString += "Error found in cogsAdmin\n"
        for cog in extensionsEconomy:
            ctx.bot.unload_extension(f'{GG.COGSECONOMY}.{cog}')
        for cog in extensionsEconomy:
            members = inspect.getmembers(cog)
            for name, member in members:
                if name.startswith('on_'):
                    ctx.bot.add_listener(member, name)
            try:
                ctx.bot.load_extension(f'{GG.COGSECONOMY}.{cog}')
            except:
                errorString += "Error found in cogsEconomy\n"
        for cog in extensionsDetermined:
            ctx.bot.unload_extension(f'cogsToBeDetermined.{cog}')
        for cog in extensionsDetermined:
            members = inspect.getmembers(cog)
            for name, member in members:
                if name.startswith('on_'):
                    ctx.bot.add_listener(member, name)
            try:
                ctx.bot.load_extension(f'cogsToBeDetermined.{cog}')
            except:
                errorString += "Error found in cogsToBeDetermined\n"

        if errorString != "":
            await ctx.respond(f'Cogs reloaded with errors:\n{errorString}', ephemeral=True)
        else:
            await ctx.respond('All cogs reloaded :white_check_mark:', ephemeral=True)

    @slash_command(name="botcheck", guild_ids=[584842413135101990])
    async def botcheck(self, ctx):
        """Does a check how many bots there are in the servers."""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        await ctx.respond(f"Checking {len(ctx.bot.guilds)} servers for bot collection servers.", ephemeral=True)
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
        await ctx.bot.change_presence(activity=discord.Game(f"with {len(ctx.bot.guilds)} servers | !help | {ctx.bot.version}"), afk=True)

    @slash_command(name="commands", guild_ids=[584842413135101990])
    async def commands(self, ctx):
        """Returns a list of all commands that are not in the database yet."""
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        nonHiddenCommands = []
        for command in self.bot.commands:
            if not command.hidden:
                nonHiddenCommands.append(command.qualified_name)
        query = {"bots": "discord", "disabled": None, "command": {"$in": nonHiddenCommands}}

        missingHelpCommands = await GG.HELP['help'].find(query).to_list(length=None)
        for command in missingHelpCommands:
            if command['command'] in nonHiddenCommands:
                nonHiddenCommands.remove(command['command'])

        await ctx.defer()
        string = ""
        for command in nonHiddenCommands:
            string += f"{command}\n"
            if len(string) > 1800:
                await ctx.send(string)
                string = ""
        await ctx.send(string)

def setup(bot):
    log.info("[Cog] Owner")
    bot.add_cog(Owner(bot))
