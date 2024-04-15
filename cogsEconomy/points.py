import typing

import discord
from discord.ext import commands

from crawler_utilities.utils.embeds import EmbedWithRandomColor
from crawler_utilities.utils.pagination import createPaginatorWithEmbeds
from crawler_utilities.utils.functions import make_ordinal, try_delete

from utils import globals as GG

log = GG.log


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
            embed.set_author(name='Points User Leaderboard', icon_url=author.display_avatar.url)
        else:
            embed.set_author(name='Points Role Leaderboard', icon_url=author.display_avatar.url)
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
            member = await ctx.guild.fetch_member(ctx.message.author.id)


        point = await GG.MDB.points.find_one({"user": member.id, "server": ctx.guild.id})
        embed = EmbedWithRandomColor()

        if ctx.author.id == member.id:
            embed.title = "Your Points"
        else:
            if member.nick is None:
                if member.name is None:
                    embed.title = f"Points for {member}"
                else:
                    embed.title = f"Points for {member.name}"
            else:
                embed.title = f"Points for {member.nick}"
        embed.set_footer(text=f"ID: {member.id}")
        if point is not None:
            embed.description = str(point['points'])
        else:
            embed.description = str(0)
        await ctx.send(embed=embed)

    @points.group(invoke_without_command=False)
    @commands.guild_only()
    async def leaderboard(self, ctx):
        pass

    @leaderboard.command(name='user', aliases=['users'])
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
            paginator = createPaginatorWithEmbeds(list)
            await paginator.respond(ctx.interaction)
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
            paginator = createPaginatorWithEmbeds(list)
            await paginator.respond(ctx.interaction)
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
        if member is None:
            member = await ctx.guild.fetch_member(ctx.message.author.id)
        point = await GG.MDB.points.find_one({"user": member.id, "server": ctx.guild.id})
        if point is not None:
            points = (amount + point['points'])
        else:
            points += amount
        await GG.MDB.points.update_one({"user": member.id, "server": ctx.guild.id}, {"$set": {"points": points}}, upsert=True)
        await ctx.send(f"{member.mention} has been given `{amount}` points.\nBringing their total to `{points}`", delete_after=5)

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

        if amount < 0:
            embed = EmbedWithRandomColor()
            embed.title = "You thought you could steal points huh?"
            embed.set_image(url="https://media1.tenor.com/images/0239cebc541822c0ece39f44a2243224/tenor.gif?itemid=9377550")
            return await ctx.send(embed=embed)

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
                                   f"Your total is `{pointsGiver}`.", delete_after=5)
                else:
                    await GG.MDB.points.update_one({"user": member.id, "server": ctx.guild.id}, {"$set": {"points": points}}, upsert=True)
                    await GG.MDB.points.update_one({"user": ctx.message.author.id, "server": ctx.guild.id}, {"$set": {"points": pointsGiver}}, upsert=True)

                    await ctx.send(f"{pointGiverUser.mention} you have given {member.mention} `{amount}` points.\n"
                                   f"Bringing their total to `{points}`, and your total is now `{pointsGiver}`", delete_after=5)
            else:
                await ctx.send(f"{pointGiverUser.mention} you don't have enough points to give `{amount}` points.\n"
                               f"You have `0` points.", delete_after=5)
        else:
            await ctx.send(f"{pointGiverUser.mention} you don't have enough points to give `{amount}` points.\n"
                           f"You have `0` points.", delete_after=5)

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
                       f"Bringing their total to `{points}`", delete_after=5)


def setup(bot):
    log.info("[Economy] Points")
    bot.add_cog(Points(bot))
