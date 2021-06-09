import asyncio
import discord
from discord.ext import commands
from disputils import BotEmbedPaginator

from utils import globals as GG
from utils import logger

log = logger.logger


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *, command=None):
        if command is not None:
            helpCommand = await GG.HELP['help'].find_one({"bots": "discord", "command": command})
            if helpCommand is not None and not helpCommand.get('disabled', False):
                prefix = await self.bot.get_server_prefix(ctx.message)
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
                await ctx.send(embed=embed)
            else:
                await ctx.send("Command doesn't exist")
        else:
            helpCommands = await GG.HELP['help'].find({"bots": "discord", "disabled": None}).to_list(length=None)
            if helpCommands is not None:
                embeds = await self.list_embed(helpCommands, ctx)
                paginator = BotEmbedPaginator(ctx, embeds)
                await paginator.run()
            else:
                return





def setup(bot):
    log.info("[Cogs] Help...")
    bot.add_cog(Help(bot))