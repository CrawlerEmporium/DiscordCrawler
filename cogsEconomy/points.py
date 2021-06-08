import typing

import discord
import utils.globals as GG
from disputils import BotEmbedPaginator

from discord.ext import commands
from utils import logger
from utils.functions import make_ordinal, try_delete

log = logger.logger


def list_embed(list_personals, author, user=True):
    embedList = []
    amount = 1
    for i in range(0, len(list_personals), 10):
        lst = list_personals[i:i + 10]
        desc = ""
        for item in lst:
            desc += f'{make_ordinal(amount)} - {str(item["name"])} - {str(item["points"])}\n'
            amount += 1
        if isinstance(author, discord.Member) and author.color != discord.Colour.default():
            embed = discord.Embed(description=desc, color=author.color)
        else:
            embed = discord.Embed(description=desc)
        if user:
            embed.set_author(name='Points User Leaderboard', icon_url=author.avatar_url)
        else:
            embed.set_author(name='Points Role Leaderboard', icon_url=author.avatar_url)
        embedList.append(embed)
    return embedList

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def points(self, ctx, member: typing.Optional[discord.Member] = None):
        '''$points [username] - Gives you the current points of [username] or yourself if no name is given.'''
        await try_delete(ctx.message)
        if member is None:
            await ctx.guild.chunk()
            member = ctx.guild.get_member(ctx.message.author.id)
        point = await GG.MDB.points.find_one({"user": member.id, "server": ctx.guild.id})
        embed = GG.EmbedWithAuthor(ctx)
        embed.title = "Points"
        if point is not None:
            embed.description = str(point['points'])
        else:
            embed.description = str(0)
        await ctx.send(embed=embed)

    @points.group(invoke_without_command=False)
    @commands.guild_only()
    async def leaderboard(self, ctx):
        pass

    @leaderboard.command(name='user')
    @commands.guild_only()
    async def user_leaderboard(self, ctx):
        '''$points leaderboard - Shows all users with points in descending order. Paged per 10.'''
        await try_delete(ctx.message)
        people = await GG.MDB.points.find({"server": ctx.guild.id, "user": {'$exists': True}}).to_list(length=None)
        if len(people) > 0:
            await ctx.guild.chunk()
            sortedList = sorted(people, key=lambda k: k['points'], reverse=True)
            embed_list = []
            for person in sortedList:
                member = ctx.guild.get_member(person['user'])
                if member is not None:
                    embed_list.append({"name": member.mention, "points": person['points']})
                else:
                    embed_list.append({"name": f"(LEFT SERVER) {person['user']}", "points": person['points']})
            list = list_embed(embed_list, ctx.message.author)
            paginator = BotEmbedPaginator(ctx, list)
            await paginator.run()
        else:
            await ctx.send("This server has nobody with points.")

    @leaderboard.command(name='role')
    @commands.guild_only()
    async def role_leaderboard(self, ctx):
        '''$points leaderboard - Shows all users with points in descending order. Paged per 10.'''
        await try_delete(ctx.message)
        people = await GG.MDB.points.find({"server": ctx.guild.id, "role": {'$exists': True}}).to_list(length=None)
        if len(people) > 0:
            await ctx.guild.chunk()
            sortedList = sorted(people, key=lambda k: k['points'], reverse=True)
            embed_list = []
            for person in sortedList:
                member = ctx.guild.get_role(person['role'])
                embed_list.append({"name": member.mention, "points": person['points']})
            list = list_embed(embed_list, ctx.message.author, user=False)
            paginator = BotEmbedPaginator(ctx, list)
            await paginator.run()
        else:
            await ctx.send("This server has no roles with points.")

    @points.command(name='add', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def add_points(self, ctx, member: typing.Optional[discord.Member], amount):
        '''$points add <username> <amount> - STAFF - Adds <amount> of points to <username>.'''
        await try_delete(ctx.message)
        points = 0
        try:
            amount = int(amount)
        except ValueError:
            await ctx.send("Please give me a number.")
            return
        point = await GG.MDB.points.find_one({"user": member.id, "server": ctx.guild.id})
        if point is not None:
            points = (amount + point['points'])
        else:
            points += amount
        await GG.MDB.points.update_one({"user": member.id, "server": ctx.guild.id}, {"$set": {"points": points}}, upsert=True)
        await ctx.send(f"You have given {member.mention} `{amount}` points.\n"
                       f"Bringing their total to `{points}`")

    @points.command(name='give', hidden=True)
    @commands.guild_only()
    async def give_points(self, ctx, member: typing.Optional[discord.Member], amount):
        '''$points give <username> <amount> - Gives <amount> of YOUR points to <username>.'''
        await try_delete(ctx.message)
        points = 0
        try:
            amount = int(amount)
        except ValueError:
            return await ctx.send("Please give me a number.")

        if ctx.message.author.id == member.id:
            return await ctx.send(f"You can't give points to yourself.")

        pointGiver = await GG.MDB.points.find_one({"user": ctx.message.author.id, "server": ctx.guild.id})
        pointGiverUser = await ctx.guild.fetch_member(ctx.message.author.id)
        if pointGiver is not None:

            pointReceiver = await GG.MDB.points.find_one({"user": member.id, "server": ctx.guild.id})
            if pointReceiver is not None:
                points = (amount + pointReceiver['points'])
            else:
                points += amount
            if pointGiver['points'] > 0:
                pointsGiver = (pointGiver['points'] - amount)
                if (pointGiver['points'] - amount) < 0:
                    await ctx.send(f"{pointGiverUser.mention} you don't have enough points to give `{amount}` points.\n"
                                   f"Your total is `{pointsGiver}`.")
                else:
                    await GG.MDB.points.update_one({"user": member.id, "server": ctx.guild.id}, {"$set": {"points": points}}, upsert=True)
                    await GG.MDB.points.update_one({"user": ctx.message.author.id, "server": ctx.guild.id}, {"$set": {"points": pointsGiver}}, upsert=True)

                    await ctx.send(f"{pointGiverUser.mention} you have given {member.mention} `{amount}` points.\n"
                                   f"Bringing their total to `{points}`, and your total is now `{pointsGiver}`")
            else:
                await ctx.send(f"{pointGiverUser.mention} you don't have enough points to give `{amount}` points.\n"
                               f"You have `0` points.")
        else:
            await ctx.send(f"{pointGiverUser.mention} you don't have enough points to give `{amount}` points.\n"
                           f"You have `0` points.")

    @points.command(name='role', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def role_points(self, ctx, role: typing.Optional[discord.Role], amount):
        '''$points role <role> <amount> - STAFF - Adds <amount> of points to <role>.'''
        await try_delete(ctx.message)
        points = 0
        try:
            amount = int(amount)
        except ValueError:
            await ctx.send("Please give me a number.")
            return
        point = await GG.MDB.points.find_one({"role": role.id, "server": ctx.guild.id})
        if point is not None:
            points = (amount + point['points'])
        else:
            points += amount
        await GG.MDB.points.update_one({"role": role.id, "server": ctx.guild.id}, {"$set": {"points": points}}, upsert=True)
        await ctx.send(f"You have given {role.mention} `{amount}` points.\n"
                       f"Bringing their total to `{points}`")


def setup(bot):
    log.info("[Economy] Points")
    bot.add_cog(Points(bot))
