import typing

import discord
import utils.globals as GG
from disputils import BotEmbedPaginator

from discord.ext import commands
from utils import logger
from utils.functions import make_ordinal

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
        people = await GG.MDB.points.find({"server": ctx.guild.id, "user": {'$exists': True}}).to_list(length=None)
        if len(people) > 0:
            await ctx.guild.chunk()
            sortedList = sorted(people, key=lambda k: k['points'], reverse=True)
            embed_list = []
            for person in sortedList:
                member = ctx.guild.get_member(person['user'])
                embed_list.append({"name": member.mention, "points": person['points']})
            list = list_embed(embed_list, ctx.message.author)
            paginator = BotEmbedPaginator(ctx, list)
            await paginator.run()
        else:
            await ctx.send("This server has nobody with points, try giving people some points before trying this command again.")

    @leaderboard.command(name='role')
    @commands.guild_only()
    async def role_leaderboard(self, ctx):
        '''$points leaderboard - Shows all users with points in descending order. Paged per 10.'''
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
            await ctx.send("This server has nobody with points, try giving people some points before trying this command again.")

    @points.command(name='add', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def add_points(self, ctx, member: typing.Optional[discord.Member], amount):
        '''$points add <username> <amount> - STAFF - Adds <amount> of points to <username>.'''
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
        await ctx.send(f"You have given {member.mention} `{amount}` points.\nBringing their total to `{points}`")

    @points.command(name='role', hidden=True)
    @GG.is_staff()
    @commands.guild_only()
    async def role_points(self, ctx, role: typing.Optional[discord.Role], amount):
        '''$points role <role> <amount> - STAFF - Adds <amount> of points to <role>.'''
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
        await ctx.send(f"You have given {role.mention} `{amount}` points.\nBringing their total to `{points}`")


def setup(bot):
    log.info("[Economy] Points")
    bot.add_cog(Points(bot))
