import requests
from discord.ext import commands

import utils.globals as GG
from utils import logger

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

                meaning_ = result['meaning']
                for x in meaning_.keys():
                    if x == "adjective":
                        try:
                            example = meaning_['adjective'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{meaning_['adjective'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (adjective)", value=definition, inline=False)
                    elif x == "exclamation":
                        try:
                            example = meaning_['exclamation'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{meaning_['exclamation'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (exclamation)", value=definition, inline=False)
                    elif x == "adverb":
                        try:
                            example = meaning_['adverb'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{meaning_['adverb'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (adverb)", value=definition, inline=False)
                    elif x == "noun":
                        try:
                            example = meaning_['noun'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{meaning_['noun'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (noun)", value=definition, inline=False)
                    elif x == "verb":
                        try:
                            example = meaning_['verb'][0]['example'].capitalize()
                        except:
                            example = "-"
                        definition = f"{meaning_['verb'][0]['definition']}\n**Example**: {example}"
                        embed.add_field(name="Description (verb)", value=definition, inline=False)
                    else:
                        owner = self.bot.get_user(GG.OWNER)
                        await owner.send(f"**MISSING KEY FOUND**\nIn the word {search}, a key was found that isn't being used: {x}.")
                if result.get('origin') is not None:
                    embed.add_field(name="Origin", value=result['origin'].capitalize(), inline=False)
                embed.set_footer(text=f"Source: Google Dictionary (Unofficial API)")
                await ctx.send(embed=embed)


def setup(bot):
    log.info("Loading Dictionary Cog...")
    bot.add_cog(Dictionary(bot))
