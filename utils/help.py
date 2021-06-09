import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

import utils.globals as GG


class Help(commands.HelpCommand):
    # !help
    async def send_bot_help(self, mapping):
        helpCommands = await GG.HELP['help'].find({"bots": "discord", "disabled": None}).to_list(length=None)
        if helpCommands is not None:
            embeds = await self.list_embed(helpCommands, self.context)
            paginator = BotEmbedPaginator(self.context, embeds)
            await paginator.run()
        else:
            return

    # !help <command>
    async def send_command_help(self, command):
        await self.getCommandHelp(command.name)

    # !help <group>
    async def send_group_help(self, group):
        await self.getCommandHelp(group.name)

    # !help <cog>
    async def send_cog_help(self, cog):
        await self.getCommandHelp(cog.name)


    async def getCommandHelp(self, command):
        helpCommand = await GG.HELP['help'].find_one({"bots": "discord", "command": command})
        if helpCommand is not None and not helpCommand.get('disabled', False):
            prefix = await self.context.bot.get_server_prefix(self.context.message)
            description = helpCommand['description'][0]
            embed = discord.Embed(title=f"{helpCommand['command'].title()}",
                                  description=f"{description.replace('{/prefix}', prefix)}")

            if len(helpCommand['syntax']) > 1:
                for i in range(len(helpCommand['syntax'])):
                    embed.add_field(name=f"Syntax {i + 1}",
                                    value=f"{helpCommand['syntax'][i].replace('{/prefix}', prefix)}", inline=False)
            else:
                embed.add_field(name=f"Syntax", value=f"{helpCommand['syntax'][0].replace('{/prefix}', prefix)}",
                                inline=False)

            if helpCommand.get('aliasFor', None) is not None:
                aliasString = ', '.join(helpCommand['aliasFor'])
                embed.add_field(name=f"Aliases", value=f"{aliasString.replace('{/prefix}', prefix)}", inline=False)

            if len(helpCommand['options']) > 1:
                for i in range(len(helpCommand['options'])):
                    entryString = '\n'.join(helpCommand['options'][i]['entries'])
                    embed.add_field(name=f"Option: {helpCommand['options'][i]['argument']}",
                                    value=f"{entryString.replace('{/prefix}', prefix)}",
                                    inline=False)
            else:
                entryString = '\n'.join(helpCommand['options'][0]['entries'])
                embed.add_field(name=f"Option: {helpCommand['options'][0]['argument']}",
                                value=f"{entryString.replace('{/prefix}', prefix)}",
                                inline=False)

            if len(helpCommand['examples']) > 1:
                exampleString = "\n".join(helpCommand['examples'])
                embed.add_field(name=f"Examples",
                                value=f"{exampleString.replace('{/prefix}', prefix)}",
                                inline=False)
            else:
                embed.add_field(name=f"Example", value=f"{helpCommand['examples'][0].replace('{/prefix}', prefix)}",
                                inline=False)

            typeString = ", ".join(helpCommand['types'])
            embed.add_field(name=f"Types", value=f"{typeString}", inline=False)

            permString = "Permissions: "
            permString += ", ".join(helpCommand['permissions'])
            embed.set_footer(text=permString)
            await self.context.send(embed=embed)
        else:
            await self.context.send("Command doesn't exist")

    async def list_embed(self, helpCommands, ctx):
        prefix = await ctx.bot.get_server_prefix(ctx.message)
        embedList = []
        for i in range(0, len(helpCommands), 10):
            commands = helpCommands[i:i + 10]
            embed = discord.Embed(title="DiscordCrawler Commands",
                                  description=f"A list of all the commands that the DiscordCrawler bot has to offer. Find out more by typing in ``{prefix}help [command]``")
            for help in commands:
                embed.add_field(name=f"{help['command']}",
                                value=f"{help['description'][0].replace('{/prefix}', prefix)}",
                                inline=False)
            embedList.append(embed)
        return embedList