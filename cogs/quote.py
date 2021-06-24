import datetime
import re
import discord
from discord.ext import commands
from crawler_utilities.utils import logger
from crawler_utilities.utils.functions import try_delete

log = logger.logger


class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['q'])
    @commands.guild_only()
    async def quote(self, ctx, msgId: int = None, *, reply=None):
        if not msgId:
            await ctx.send(content=":x:" + ' **Please provide a valid message argument.**')
            return

        if not isinstance(msgId, int):
            await ctx.send(content=":x:" + " **I work only with message Id's.**")
            return

        await try_delete(ctx.message)

        message = None
        try:
            msgId = int(msgId)
            perms = ctx.guild.me.permissions_in(ctx.channel)
        except ValueError:
            if perms.read_messages and perms.read_message_history:
                async for msg in ctx.channel.history(limit=100, before=ctx.message):
                    if msgId.lower() in msg.content.lower():
                        message = msg
                        break
        else:
            try:
                message = await ctx.channel.fetch_message(msgId)
            except:
                for channel in ctx.guild.text_channels:
                    perms = ctx.guild.me.permissions_in(channel)
                    if channel == ctx.channel or not perms.read_messages or not perms.read_message_history:
                        continue

                    try:
                        message = await channel.fetch_message(msgId)
                    except:
                        continue
                    else:
                        break

        if message:
            if not message.content and message.embeds and message.author.bot:
                await ctx.send(
                    content='Raw embed from `' + str(message.author).strip('`') + '` in ' + message.channel.mention,
                    embed=quote_embed(ctx.channel, message, ctx.author))
            else:
                await ctx.send(embed=quote_embed(ctx.channel, message, ctx.author))

            if reply:
                if perms.manage_webhooks:
                    webhook = await ctx.channel.create_webhook(name="Quoting")
                    await webhook.send(content=reply.replace('@everyone', '@еveryone').replace('@here', '@hеre'),
                                       username=ctx.author.display_name, avatar_url=ctx.author.avatar_url)
                    await webhook.delete()
                else:
                    await ctx.send(
                        content='**' + ctx.author.display_name + '\'s reply:**\n' + reply.replace('@everyone',
                                                                                                  '@еveryone').replace(
                            '@here', '@hеre'))
        else:
            await ctx.send(content=":x:" + ' **Could not find the specified message.**')


def parse_time(timestamp):
    if timestamp:
        return datetime.datetime(*map(int, re.split(r'[^\d]', timestamp.replace('+00:00', ''))))
    return None


def quote_embed(context_channel, message, user):
    if not message.content and message.embeds and message.author.bot:
        embed = message.embeds[0]
    else:
        uri = 'https://discordapp.com/channels/' + str(message.guild.id) + '/' + str(
            message.channel.id) + '/' + str(
            message.id)

        if message.channel != context_channel:
            message.content += f"\nQuoted by: {user} | in channel: #{message.channel.name} | [Direct Link]({uri})"
        else:
            message.content += f"\nQuoted by: {user} | [Direct Link]({uri})"

        if message.author not in message.guild.members or message.author.color == discord.Colour.default():
            embed = discord.Embed(description=message.content)
        else:
            embed = discord.Embed(description=message.content, color=message.author.color)
        if message.attachments:
            if message.channel.is_nsfw() and not context_channel.is_nsfw():
                embed.add_field(name='Attachments', value=':underage: **Quoted message belongs in NSFW channel.**')
            elif len(message.attachments) == 1 and message.attachments[0].url.lower().endswith(
                    ('.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webp', '.bmp')):
                embed.set_image(url=message.attachments[0].url)
            else:
                for attachment in message.attachments:
                    embed.add_field(name='Attachment', value='[' + attachment.filename + '](' + attachment.url + ')',
                                    inline=False)

        embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)

    return embed


def setup(bot):
    log.info("[Cog] Quote")
    bot.add_cog(Quote(bot))
