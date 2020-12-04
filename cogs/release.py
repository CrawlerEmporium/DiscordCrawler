import asyncio
import typing
import discord
from discord import Embed
from discord.ext import commands
from utils import logger
from enum import Enum
from utils import globals as GG

log = logger.logger


class State(Enum):
    NEW = 0
    TITLE = 1
    SUBTITLE = 2
    SOURCE = 3
    LINK = 4
    TYPE = 5
    META = 6
    AUTHORS = 7
    CREDITS = 8
    DONE = 9


class Release(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @GG.is_cleaner()
    async def update(self, ctx, msg_arg = None, type = "", *, editedContent):
        """Update a prior release. type can be one of the following:
        TITLE
        SUBTITLE
        SOURCE
        LINK
        TYPE
        META
        AUTHORS
        CREDITS
        IMAGE (must be an url)"""
        message = None
        try:
            msg_arg = int(msg_arg)
        except ValueError:
            perms = ctx.guild.me.permissions_in(ctx.channel)
            if perms.read_messages and perms.read_message_history:
                async for msg in ctx.channel.history(limit=100, before=ctx.message):
                    if msg_arg.lower() in msg.content.lower():
                        message = msg
                        break
        else:
            try:
                message = await ctx.channel.fetch_message(msg_arg)
            except:
                for channel in ctx.guild.text_channels:
                    perms = ctx.guild.me.permissions_in(channel)
                    if channel == ctx.channel or not perms.read_messages or not perms.read_message_history:
                        continue

                    try:
                        message = await channel.fetch_message(msg_arg)
                    except:
                        continue
                    else:
                        break
        if message:
            release = ReleaseModel()
            for x in message.embeds[0].fields:
                if x.name == "Title":
                    release.title = x.value
                if x.name == "Subtitle":
                    release.subtitle = x.value
                if x.name == "Source":
                    release.source = x.value
                if x.name == "Download Link" or x.name == "Link":
                    release.link = x.value
                if x.name == "Type":
                    release.type = x.value
                if x.name == "Meta Tag(s)":
                    release.meta = x.value
                if x.name == "Author(s)":
                    release.authors = x.value
                if x.name == "Donated By" or x.name == "Credits":
                    release.credits = x.value
            if message.embeds[0].image != None:
                release.image_url = message.embeds[0].image.proxy_url

            if type == "TITLE":
                release.title = editedContent
            if type == "SUBTITLE":
                release.subtitle = editedContent
            if type == "SOURCE":
                await asyncio.sleep(5)
                for x in ctx.message.embeds:
                    release.image_url = x.thumbnail.proxy_url
                release.source = editedContent
            if type == "LINK":
                release.link = editedContent
            if type == "TYPE":
                release.type = editedContent
            if type == "META":
                release.meta = editedContent
            if type == "AUTHORS":
                release.authors = editedContent
            if type == "CREDITS":
                release.credits = editedContent
            if type == "IMAGE":
                release.image_url = editedContent

            await self.sendReleaseEmbed(message, release)
            await ctx.message.delete()


    @commands.command()
    @GG.is_cleaner()
    async def release(self, ctx):
        release = ReleaseModel()
        release.state = State.TITLE
        await ctx.message.delete()
        message = await ctx.send(f"First, give me the title of the release you want to add.")
        await self.waitReleaseMessage(ctx, message, release)

    async def waitReleaseMessage(self, ctx, message, release):
        def check(reply):
            return (reply.author == ctx.message.author)

        try:
            if release.state == State.TITLE:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.SUBTITLE
                await message.edit(
                    content=f"If the Title has a Subtitle, please enter it now. If it doesn't have anything reply with a `-`")
                release.title = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.SUBTITLE:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.SOURCE
                await message.edit(content=f"Enter the source link to the Title.")
                release.subtitle = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.SOURCE:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                for x in reply.embeds:
                    release.image_url = x.thumbnail.proxy_url
                release.state = State.LINK
                await message.edit(content=f"Enter the download link of the Title.")
                release.source = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.LINK:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.TYPE
                await message.edit(content=f"Now give me the type or types of the book. Ie. Campaign, Class, or Race.")
                release.link = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.TYPE:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.META
                await message.edit(
                    content=f"If the Type has a subcategory, ie. for class it's about sorcerers, add it here. If it doesn't have any reply with a `-`")
                release.type = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.META:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.AUTHORS
                await message.edit(content=f"I'd like the Authors of the Title now, separate them with a comma.")
                release.meta = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.AUTHORS:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.CREDITS
                await message.edit(
                    content=f"Was this Title donated by anyone? This field is not required, so reply with `-` if you want this empty.")
                release.authors = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.CREDITS:
                reply = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                release.state = State.DONE
                release.credits = reply.content
                await reply.delete()
                await self.waitReleaseMessage(ctx, message, release)

            elif release.state == State.DONE:
                await self.sendReleaseEmbed(message, release)


        except asyncio.TimeoutError:
            msg = ctx.send("Release was not completed in time. Please try again.")
            await msg.delete(delay=15)

    async def sendReleaseEmbed(self, message, release):
        log.info(f"New Release:\n{release}")
        em = discord.Embed()
        em.add_field(name=f"Title", value=f"{release.title}", inline=False)
        if release.subtitle != "-":
            em.add_field(name=f"Subtitle", value=f"{release.subtitle}", inline=False)
            em.title = f"{release.title}: {release.subtitle}"
        else:
            em.title = f"{release.title}"
        em.add_field(name=f"Source", value=f"{release.source}", inline=False)
        em.add_field(name=f"Download Link", value=f"{release.link}", inline=False)
        em.add_field(name=f"Type", value=f"{release.type}", inline=False)
        if release.meta != "-":
            em.add_field(name=f"Meta Tag(s)", value=f"{release.meta}", inline=False)
        em.add_field(name=f"Author(s)", value=f"{release.authors}", inline=False)
        if release.credits != "-":
            em.add_field(name=f"Donated By", value=f"{release.credits}", inline=False)
        if release.image_url != "" and release.image_url != "-":
            em.set_image(url=release.image_url)
        await message.edit(content=None, embed=em)


def setup(bot):
    log.info("[Cog] Releases")
    bot.add_cog(Release(bot))


class ReleaseModel:
    def __init__(self, title="", subtitle="-", source="", link="", type="", meta="-", authors="", credits="-",
                 image_url="-"):
        self.title = title
        self.subtitle = subtitle
        self.source = source
        self.image_url = image_url
        self.link = link
        self.type = type
        self.meta = meta
        self.authors = authors
        self.credits = credits
        self.state = State.NEW

    def __repr__(self):
        return "Title: %s\nSubtitle: %s\nSource: %s\nLink: %s\nType: %s\nMeta: %s\nAuthors: %s\nCredits: %s\nImage_Url: %s" % (self.title, self.subtitle, self.source, self.link, self.type, self.meta, self.authors, self.credits, self.image_url)