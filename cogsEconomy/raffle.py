import asyncio
import random

import discord
import utils.globals as GG

from discord.ext import commands
from crawler_utilities.handlers import logger
from crawler_utilities.utils.confirmation import BotConfirmation

from crawler_utilities.utils.functions import try_delete, get_next_num

log = logger.logger


class Raffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commands

    @commands.group(invoke_without_command=False)
    async def raffle(self, ctx):
        pass

    @raffle.command(name='create')
    @commands.guild_only()
    @GG.is_staff()
    async def raffle_create(self, ctx, cost: int = 10, totalTickets: int = 0):
        """$raffle create <cost> [totalTickets] - STAFF - Creates a new raffle, that sells tickets for <amount> of points.\nIf [totalTickets] is filled, raffle will have a finite amount of buyable tickets."""
        id = await get_next_num(self.bot.mdb['properties'], 'raffleId')
        title = "New Raffle!"
        description = ""
        embed = self.createRaffleEmbed(title, description, id, totalTickets, cost)
        msg = await ctx.send(embed=embed)

        if totalTickets == 0:
            self.bot.mdb['raffle'].insert_one({"id": int(id), "msgId": f"{msg.id}", "channelId": f"{ctx.message.channel.id}", "serverId": f"{ctx.guild.id}", "title": title, "description": description, "cost": cost, "boughtTickets": 0, "ended": 0})
        else:
            self.bot.mdb['raffle'].insert_one({"id": int(id), "msgId": f"{msg.id}", "channelId": f"{ctx.message.channel.id}", "serverId": f"{ctx.guild.id}", "title": title, "description": description, "cost": cost, "totalTickets": totalTickets, "boughtTickets": 0, "ended": 0})

    @raffle.command(name='title')
    @commands.guild_only()
    @GG.is_staff()
    async def raffle_title(self, ctx, id: int, *, title):
        """$raffle title <id> <title> - STAFF - Edits the title for <id> raffle."""
        if id == 0:
            await try_delete(ctx.message)
            return
        else:
            raffle = await self.bot.mdb['raffle'].find_one({'id': int(id)})
            if raffle is not None:
                await try_delete(ctx.message)
                raffle['title'] = title
                totalTickets = raffle.get('totalTickets', 0)
                embed = self.createRaffleEmbed(raffle['title'], raffle['description'], raffle['id'], totalTickets, raffle['cost'])
                guild = ctx.guild
                ch = guild.get_channel(int(raffle['channelId']))
                message = await ch.fetch_message(int(raffle['msgId']))
                await message.edit(content=None, embed=embed)
                await self.bot.mdb['raffle'].replace_one({"id": raffle['id']}, raffle)
                await ctx.send(f"Title of raffle `{id}` was changed to: `{title}`.")
            else:
                await ctx.send(f"Raffle with Id `{id}` not found.")
                await try_delete(ctx.message)

    @raffle.command(name='desc')
    @commands.guild_only()
    @GG.is_staff()
    async def raffle_desc(self, ctx, id: int, *, description):
        """$raffle desc <id> <description> - STAFF - Edits the description for <id> raffle."""
        if id == 0:
            await try_delete(ctx.message)
            return
        else:
            raffle = await self.bot.mdb['raffle'].find_one({'id': int(id)})
            if raffle is not None:
                await try_delete(ctx.message)
                raffle['description'] = description
                totalTickets = raffle.get('totalTickets', 0)
                embed = self.createRaffleEmbed(raffle['title'], raffle['description'], raffle['id'], totalTickets, raffle['cost'])
                guild = ctx.guild
                ch = guild.get_channel(int(raffle['channelId']))
                message = await ch.fetch_message(int(raffle['msgId']))
                await message.edit(content=None, embed=embed)
                await self.bot.mdb['raffle'].replace_one({"id": raffle['id']}, raffle)
                await ctx.send(f"Description of raffle `{id}` was changed to: `{description}`.")
            else:
                await ctx.send(f"Raffle with Id `{id}` not found.")
                await try_delete(ctx.message)

    @raffle.command(name='pull')
    @commands.guild_only()
    @GG.is_staff()
    async def raffle_pull(self, ctx, id: int, winners: int = 1):
        """$raffle pull <id> [amountOfWinners]- STAFF - Pulls a winner or [amountOfWinners] from <id> raffle."""
        raffle = await self.bot.mdb['raffle'].find_one({'id': int(id)})
        if raffle is not None:
            if raffle['ended'] == 1:
                await ctx.send(f"Raffle with Id `{id}` has already ended (or was canceled).")
                return
            else:
                entries = await self.bot.mdb['raffleEntries'].find({"raffleId": id, "serverId": ctx.guild.id}).to_list(length=None)
                if entries is not None:
                    if winners > len(entries):
                        await ctx.send("You have selected more winners for the raffle than there are entries. Please lower your total winners or wait until enough tickets are bought.\n"
                                       f"{len(entries)} tickets were bought, this does not factor in duplicate entrants.")
                        return

                    winnersList = []
                    for winner in range(winners):
                        entry = random.choice(entries)
                        winnersList.append(entry)
                        entries.remove(entry)

                    embed = discord.Embed()
                    if len(winnersList) == 1:
                        embed.title = "We have a winner!"
                        embed.description = f"A winner was chosen for `{raffle['title']}`\nA total of `{len(entries)}` entries were purchased!"
                    else:
                        embed.title = "We have winners!"
                        embed.description = f"{len(winnersList)} were chosen for `{raffle['title']}`\nA total of `{len(entries)}` entries were purchased!"
                    for x in winnersList:
                        user = await self.bot.get_guild(x['serverId']).fetch_member(x['userId'])
                        embed.add_field(name="Winner", value=user.mention)

                    await ctx.send(embed=embed)
                    raffle['ended'] = 1
                    await self.bot.mdb['raffle'].replace_one({"id": raffle['id']}, raffle)

                else:
                    await ctx.send(f"No tickets were bought. Wait until tickets or bought, or cancel the raffle.")
        else:
            await ctx.send(f"Raffle with Id `{id}` not found.")
            await try_delete(ctx.message)

    @raffle.command(name='enter')
    @commands.guild_only()
    async def raffle_enter(self, ctx, id: int, tickets: int = 1):
        """$raffle enter <id> [tickets] - Enters a raffle, buying [tickets] amount of tickets if specified, otherwise 1."""
        await try_delete(ctx.message)
        raffle = await self.bot.mdb['raffle'].find_one({'id': int(id)})
        if raffle is not None:
            if raffle['ended'] == 1:
                await ctx.send(f"Raffle with Id `{id}` has already ended (or was canceled).")
                return
            else:
                user = await GG.MDB.points.find_one({"user": ctx.author.id, "server": ctx.guild.id})
                if user is not None:
                    userPoints = user['points']
                    userId = user['user']
                    serverId = user['server']
                    raffleId = raffle['id']
                    cost = raffle['cost']
                    totalCostTickets = cost * tickets

                    if userPoints < totalCostTickets:
                        await ctx.send(f"You don't have enough points to purchase `{tickets}` tickets.\n"
                                       f"You wanted to purchase `{tickets}` ticket(s), and they cost `{cost}` points a piece, totalling to `{totalCostTickets}` points.\n"
                                       f"Your total current points however are `{userPoints}`. This means you are `{totalCostTickets - userPoints}` points short.")
                        return

                    totalTickets = raffle.get('totalTickets', None)
                    if totalTickets is not None:
                        if totalTickets < tickets:
                            await ctx.send(f"There aren't enough tickets to purchase.\nThere are `{totalTickets}` remaining tickets in this raffle.")
                            return

                    for x in range(tickets):
                        raffleEntry = {
                            "raffleId": raffleId,
                            "serverId": serverId,
                            "userId": userId,
                            "ticketCost": cost
                        }
                        await self.bot.mdb['raffleEntries'].insert_one(raffleEntry)
                    await GG.MDB.points.update_one({"user": userId, "server": ctx.guild.id}, {"$set": {"points": (userPoints - totalCostTickets)}}, upsert=True)
                    await ctx.send(f"You have purchased `{tickets}` tickets for raffle `{raffleId}`, costing a total of `{totalCostTickets}` points.\nYou have `{userPoints - totalCostTickets}` points left.")
                else:
                    await ctx.send(f"You have no points, so you are not able to enter this raffle.")
        else:
            await ctx.send(f"Raffle with Id `{id}` not found.")

    @raffle.command(name='cancel')
    @commands.guild_only()
    @GG.is_staff()
    async def raffle_cancel(self, ctx, id: int = 0):
        """$raffle cancel <id> - STAFF - Stops the <id> raffle, without pulling a winner, will refund all tickets."""
        if id == 0:
            await try_delete(ctx.message)
            return
        else:
            raffle = await self.bot.mdb['raffle'].find_one({'id': int(id)})
            if raffle is not None:
                await try_delete(ctx.message)
                if raffle['ended'] == 0:
                    confirmation = BotConfirmation(ctx, 0x012345)
                    await confirmation.confirm(f"Are you sure you want to cancel the raffle with id: ({raffle['id']})?")
                    if confirmation.confirmed:
                        ch = ctx.guild.get_channel(int(raffle['channelId']))
                        await ctx.send(f"Raffle with id {raffle['id']} was canceled. Refunding all tickets to their buyers...")

                        # Refund Tickets to buyers
                        entries = await self.bot.mdb['raffleEntries'].find({"raffleId": id, "serverId": ctx.guild.id}).to_list(length=None)
                        if entries is not None:
                            for entry in entries:
                                user = await GG.MDB.points.find_one({"user": entry['userId'], "server": ctx.guild.id})
                                await GG.MDB.points.update_one({"user": entry['userId'], "server": ctx.guild.id}, {"$set": {"points": (user['points'] + entry['ticketCost'])}}, upsert=True)
                            await self.bot.mdb['raffleEntries'].delete_many({"raffleId": id, "serverId": ctx.guild.id})

                        message = await ch.fetch_message(int(raffle['msgId']))
                        await try_delete(message)
                        raffle['ended'] = 1
                        await self.bot.mdb['raffle'].replace_one({"id": raffle['id']}, raffle)
                        await asyncio.sleep(8)
                        await confirmation.quit()
                    else:
                        await confirmation.quit()
                else:
                    await ctx.send("This raffle was already canceled or is already ended.")
            else:
                await ctx.send(f"Raffle with Id `{id}` not found.")
                await try_delete(ctx.message)

    # Functions
    def createRaffleEmbed(self, title, description, id, totalTickets, cost):
        embed = discord.Embed()
        embed.title = title
        if description != "":
            embed.description = description
        embed.add_field(name="Tickets Cost", value=f"{cost} points", inline=False)
        if totalTickets == 0:
            embed.add_field(name="Tickets available", value="No limit!", inline=False)
        else:
            embed.add_field(name="Tickets available", value=f"{totalTickets}", inline=False)

        embed.add_field(name="Instructions", value=f"Check your points available with the `points` command.\n"
                                                   f"To buy a ticket use ``raffle enter {id}``, if you want multiple use ``raffle enter {id} amountYouWish``.", inline=False)
        embed.set_footer(text=f"Id: {id}")
        return embed


def setup(bot):
    log.info("[Economy] Raffle")
    bot.add_cog(Raffle(bot))
