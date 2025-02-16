import discord
from discord import slash_command
from discord.ext import commands

from utils import globals as GG
from utils.checks import is_staff_trouble, is_trouble

log = GG.log


def singleOrMulti(length):
    if length >= 2:
        return ["posts", "were", "are"]
    else:
        return ["post", "was", "is"]


def formatMessage(message):
    fMessage = {}
    if message.content == "":
        if len(message.attachments) > 0:
            fMessage['content'] = "Attachment"
        else:
            fMessage['content'] = message.content
    fMessage['user'] = message.author.display_name
    fMessage['id'] = message.id

    return fMessage


async def fetchRecentMessages(bot, channelId):
    channel = bot.get_channel(channelId)
    history = await channel.history(limit=25).flatten()
    messages = []

    for message in history:
        messages.append(formatMessage(message))

    return messages


async def nudged_embed(original_message):
    embed = discord.Embed(description=original_message.content)
    embed.set_author(name=original_message.author.display_name,
                     icon_url=original_message.author.avatar.url if original_message.author.avatar else None)
    embed.set_footer(text=f"Moved from #{original_message.channel}")
    return embed


async def nudged_embed_formatted(fMsg):
    embed = discord.Embed(description=fMsg.content)
    embed.set_author(name=fMsg.author.display_name,
                     icon_url=fMsg.author.avatar.url if fMsg.author.avatar else None)
    embed.set_footer(text=f"Moved from #{fMsg.channel}")
    return embed


class Nudge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Nudge Message")
    @commands.guild_only()
    async def _Nudge(self, ctx, message: discord.Message):
        await ctx.defer(ephemeral=True)
        if not is_trouble(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        view = ChannelSelectView(message)
        await ctx.respond(f"Where do you want to nudge this message to?", view=view)

    @slash_command(name="nudge", description="Nudge one or more messages to a channel of choice.")
    @commands.guild_only()
    async def nudge(self, ctx):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_trouble_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        view = MessageSelectView(fetchRecentMessages(self.bot, ctx.channel))
        await ctx.respond(f"Where do you want to nudge this message to?", view=view)


def setup(bot):
    log.info("[Cog] Nudge")
    bot.add_cog(Nudge(bot))


class ChannelSelectView(discord.ui.View):
    def __init__(self, original_message):
        super().__init__()
        self.original_message = original_message

    @discord.ui.channel_select(placeholder="Select a channel...", min_values=1, max_values=1,
                               channel_types=[discord.ChannelType.text])
    async def callback(self, select, interaction: discord.Interaction) -> None:
        channel_id = int(select.values[0].id)
        target_channel = self.original_message.guild.get_channel(channel_id)

        if not target_channel:
            return await interaction.response.send_message("Invalid channel selected.", ephemeral=True)

        embed = await nudged_embed(self.original_message)

        await target_channel.send(content=self.original_message.author.mention, embed=embed)

        await self.original_message.delete()

        await interaction.edit(content=f"Message moved to {target_channel.mention}", view=None)


class MessageSelectView(discord.ui.Select):
    def __init__(self, recent_messages):
        options = [discord.SelectOption(label=msg.user, description=msg.content[0:100], value=msg.id) for msg in
                   recent_messages]

        super().__init__(
            placeholder="Select message(s)",
            min_values=1,
            max_values=25,
            options=options
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        messages = self.values

        view = MultipleMessagesChannelSelectView(messages)
        await interaction.respond(f"Where do you want to nudge these messages to?", view=view)


class MultipleMessagesChannelSelectView(discord.ui.View):
    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    @discord.ui.channel_select(placeholder="Select a channel...", min_values=1, max_values=1,
                               channel_types=[discord.ChannelType.text])
    async def callback(self, select, interaction: discord.Interaction) -> None:
        channel_id = int(select.values[0].id)
        target_channel = await interaction.guild.fetch_channel(channel_id)

        if not target_channel:
            return await interaction.response.send_message("Invalid channel selected.", ephemeral=True)

        for msg in self.messages:
            orig_chnl = await interaction.guild.fetch_channel(msg.channel.id)
            orig_msg = await orig_chnl.fetch_message(msg.id)

            embed = await nudged_embed_formatted(orig_msg)
            await target_channel.send(embed=embed)
            await orig_msg.delete()

        await interaction.edit(content=f"Messages moved to {target_channel.mention}", view=None)
