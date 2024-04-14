import random

import discord

from discord.ext import commands, tasks
from utils import globals as GG
from crawler_utilities.utils.functions import safeEmbed

log = GG.log


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveawayMessages = []
        self.giveawayCheck.start()

    @tasks.loop(count=1)
    async def giveawayCheck(self):
        for x in await GG.MDB['giveaway'].find({}).to_list(length=None):
            self.giveawayMessages.append(int(x['msgId']))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = payload.emoji
        user = payload.user_id

        if user != 602774912595263490:
            if payload.message_id in self.giveawayMessages:
                if emoji.name == "✅":
                    giveaway = await GG.MDB['giveaway'].find_one({'msgId': f'{payload.message_id}'})
                    signed = await GG.MDB['giveawaySignUp'].find_one({'user': f'{user}', 'id': f'{int(giveaway["id"])}'})
                    if not signed:
                        await GG.MDB['giveawaySignUp'].insert_one({'user': f'{user}', 'id': f'{int(giveaway["id"])}'})

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emoji = payload.emoji
        user = payload.user_id
        if user != 602774912595263490:
            if payload.message_id in self.giveawayMessages:
                if emoji.name == "✅":
                    giveaway = await GG.MDB['giveaway'].find_one({'msgId': f'{payload.message_id}'})
                    signed = await GG.MDB['giveawaySignUp'].find_one({'user': f'{user}', 'id': f'{int(giveaway["id"])}'})
                    if signed:
                        await GG.MDB['giveawaySignUp'].delete_one({'user': f'{user}', 'id': f'{int(giveaway["id"])}'})

    @commands.command()
    async def giveaway(self, ctx, *, desc):
        id, msg = await self.sendEmbed(ctx, ctx.author.display_name, desc)
        await GG.MDB['giveaway'].insert_one({'id': f'{int(id)}', 'msgId': f'{msg.id}', 'author': f'{ctx.author.id}', 'pulled': False})
        self.giveawayMessages.append(int(msg.id))
        await ctx.message.delete()

    @commands.command()
    async def pull(self, ctx, id=0, winners=1):
        if id == 0:
            await ctx.message.delete()
            return
        else:
            giveaway = await GG.MDB['giveaway'].find_one({'id': str(id)})
            if giveaway is not None:
                if giveaway['author'] == str(ctx.author.id) and giveaway['pulled'] is not True:
                    giveaway['pulled'] = True
                    await GG.MDB['giveaway'].replace_one({"id": f"{str(giveaway['id'])}"}, giveaway)

                    entries = await GG.MDB['giveawaySignUp'].find({"id": str(id)}).to_list(length=None)
                    if len(entries) > 0:
                        winnerList = []

                        if len(entries) < winners:
                            winners = len(entries)

                        for x in range(winners):
                            entry = random.choice(entries)
                            if entry not in winnerList:
                                winnerList.append(entry)
                            else:
                                while entry not in winnerList:
                                    entry = random.choice(entries)
                                    if entry not in winnerList:
                                        winnerList.append(entry)

                        embed_queue = [discord.Embed()]
                        if len(winnerList) == 1:

                            embed_queue[-1].title = "We have a winner!"
                            embed_queue[-1].description = f"A winner was chosen!"
                        else:
                            embed_queue[-1].title = "We have winners!"
                            embed_queue[-1].description = f"Multiple winners were chosen!"

                        winnerString = ""
                        for entry in winnerList:
                            user = await self.bot.get_guild(ctx.guild.id).fetch_member(entry['user'])
                            winnerString += f"{user.mention}\n"

                        await safeEmbed(embed_queue, "Winner(s)", winnerString, embed_queue[-1].colour)

                        print(embed_queue)

                        for embed in embed_queue:
                            await ctx.send(embed=embed)

                        message = await ctx.channel.fetch_message(int(giveaway['msgId']))
                        await message.delete()

                        await ctx.message.delete()
                    else:
                        await ctx.message.delete()
                else:
                    await ctx.message.delete()
            else:
                await ctx.message.delete()

    async def sendEmbed(self, ctx, author, desc):
        id = await self.get_next_schedule_num()
        embed = discord.Embed()
        embed.title = f"Giveaway!"
        embed.colour = random.randint(0, 0xffffff)
        embed.description = f"{desc}"
        embed.add_field(name="Hosted by", value=f"{author}", inline=False)
        embed.add_field(name="Instructions", value="Clicking the ✅ below will enter you into this giveaway.", inline=False)
        embed.set_footer(text=f"Id: {id} • To end this giveaway run the command !pull {id}")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        return id, msg

    async def get_next_schedule_num(self):
        reportNum = await GG.MDB['properties'].find_one({'key': 'giveawayId'})
        num = reportNum['amount'] + 1
        reportNum['amount'] += 1
        await self.bot.mdb['properties'].replace_one({"key": 'giveawayId'}, reportNum)
        return f"{num}"


def setup(bot):
    log.info("[Cog] Giveaway...")
    bot.add_cog(Giveaway(bot))
