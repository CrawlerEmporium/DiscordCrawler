import asyncio
import discord
import utils.globals as GG
import requests
from discord.ext import commands
from utils import logger
from DBService import DBService

log = logger.logger

DATA_SRC = "https://googledictionaryapi.eu-gb.mybluemix.net/?define="


class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['dict', 'define'])
    async def dictionary(self, ctx, *, search):
        with requests.Session() as s:
            resp = s.get(DATA_SRC + search)
            try:
                result = resp.json()
            except:
                await ctx.send(
                    f"One of the following three errors occurred (in order of most likely happening)\n"
                    f"1. I have reached my API calls per minute, please try again in a bit.\n"
                    f"2. Google Dictionary does not contain a definition of your search query (`{search}`)\n"
                    f"3. You might have made a typo...\n"
                    f"All 3 options are easily verifiable through Google itself.")
            else:
                result = result[0]

                word = result['word']
                phonetic = result['phonetic']

                embed = GG.EmbedWithAuthor(ctx)
                embed.title = word.capitalize()
                embed.description = phonetic
                for x in result.get('meaning'):
                    if "adjective" in x:
                        try:
                            example = result['meaning']['adjective'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{result['meaning']['adjective'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (adjective)",value=definition, inline=False)
                    elif "noun" in x:
                        try :
                            example = result['meaning']['noun'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{result['meaning']['noun'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (noun)", value=definition,inline=False)
                    elif "verb" in x:
                        try:
                            example = result['meaning']['verb'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{result['meaning']['verb'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (verb)", value=definition,inline=False)
                if result.get('origin') is not None:
                    embed.add_field(name="Origin", value=result['origin'].capitalize(),inline=False)
                embed.set_footer(text=f"Source: Google Dictionary")
                await ctx.send(embed=embed)


def setup(bot):
    log.info("Loading Dictionary Cog...")
    bot.add_cog(Dictionary(bot))
