import requests
from discord.ext import commands

import utils.globals as GG
from utils import logger

log = logger.logger

DATA_SRC = "https://api.dictionaryapi.dev/api/v1/entries/en/"


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
                for i in range(len(result)):
                    current = result[i]

                    word = current['word']
                    try:
                        phonetic = ""
                        phonetic_ = current['phonetics']
                        for x in phonetic_:
                            phonetic += x['text'] + ", "
                    except:
                        phonetic = "no pronunciation available."

                    phonetic = phonetic[:-2]

                    embed = GG.EmbedWithAuthor(ctx)
                    embed.title = word.capitalize()
                    embed.description = phonetic

                    meaning_ = current['meaning']
                    for x in meaning_.keys():
                        await self.getExampleAndDefinition(embed, meaning_, x)
                    if current.get('origin') is not None:
                        embed.add_field(name="Origin", value=current['origin'].capitalize(), inline=False)
                    embed.set_footer(text=f"Source: Google Dictionary (Unofficial API)")
                    await ctx.send(embed=embed)

    async def getExampleAndDefinition(self, embed, meaning_, x):
        for y in range(len(meaning_[f'{x}'])):
            try:
                example = meaning_[f'{x}'][y]['example'].capitalize()
            except:
                example = "-"
            try:
                definition = f"{meaning_[f'{x}'][y]['definition']}\n**Example**: {example}"
                embed.add_field(name=f"Description ({x})", value=definition, inline=False)
            except:
                definition = f"**Example**: {example}"
                embed.add_field(name=f"** **", value=definition, inline=False)


def setup(bot):
    log.info("[Cog] Dictionary")
    bot.add_cog(Dictionary(bot))
