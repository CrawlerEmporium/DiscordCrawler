import discord

from discord import slash_command
from discord.ext import commands

from modals.Anonymous import Anonymous
from utils import globals as GG

log = GG.log


class AnonModal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="anonreport")
    @commands.guild_only()
    async def anonreport(self, ctx):
        """Opens a modal to post an anonymous report."""
        delivery_channel = await GG.MDB['channelinfo'].find_one({"guild": ctx.interaction.guild_id, "type": "DELIVERY"})
        if delivery_channel is None:
            await self.noDeliveryChannel(ctx.interaction.guild, ctx.interaction)
            await self.notifyOwner(ctx.interaction.guild, ctx.interaction)
            return

        thread_channel = await GG.MDB['channelinfo'].find_one({"guild": ctx.interaction.guild_id, "type": "ANON"})
        if thread_channel is None:
            await self.noThreadChannel(ctx.interaction.guild, ctx.interaction)
            await self.notifyOwner(ctx.interaction.guild, ctx.interaction)
            return

        delivery_channel = await self.bot.fetch_channel(delivery_channel['channel'])
        thread_channel = await self.bot.fetch_channel(thread_channel['channel'])
        modal = Anonymous(self.bot, ctx.interaction, ctx.interaction.user, delivery_channel, thread_channel)
        await ctx.interaction.response.send_modal(modal)

    async def notifyOwner(self, guild, interaction_for_modal=None):
        ServerOwner = self.bot.get_user(guild.owner.id)
        if ServerOwner.dm_channel is None:
            dm_channel = await ServerOwner.create_dm()
        else:
            dm_channel = ServerOwner.dm_channel
        Embed = discord.Embed(title=f"No delivery channel and/or thread channel exists.",
                              description=f"Hello, a user of your server {guild.name} tried to make an "
                                          f"anonymous report, but you have yet to make a delivery channel and/or thread channel. You can do this by "
                                          f"executing the following command: ``/addchannel <id> DELIVERY`` and/or ``/addchannel <id> ANON``. Thank you!")
        try:
            await dm_channel.send(embed=Embed)
        except discord.Forbidden:
            if interaction_for_modal is not None:
                await interaction_for_modal.channel.send(
                    f"Hello {guild.owner.mention}, a user just tried to make an anonymous report, but you have "
                    f"yet to make a delivery channel. You can do this by executing the following command: ``/addchannel "
                    f"<id> DELIVERY``. Thank you!")

    async def noThreadChannel(self, guild, interaction_for_modal=None):
        Reporter = self.bot.get_user(interaction_for_modal.user.id)
        if Reporter.dm_channel is None:
            dm_channel = await Reporter.create_dm()
        else:
            dm_channel = Reporter.dm_channel
        Embed = discord.Embed(title=f"Error",
                              description="Sorry this Server doesnt have a thread channel yet, "
                                          "I will notify the Server Owner for you if I'm able.")
        try:
            await dm_channel.send(embed=Embed)
        except discord.Forbidden:
            if interaction_for_modal is not None:
                await interaction_for_modal.channel.send(
                    "@Reporter, you have turned off the ability to let me DM you. I will notify the "
                    "Server Owner that they haven't created a delivery channel yet.")

    async def noDeliveryChannel(self, guild, interaction_for_modal=None):
        Reporter = self.bot.get_user(interaction_for_modal.user.id)
        if Reporter.dm_channel is None:
            dm_channel = await Reporter.create_dm()
        else:
            dm_channel = Reporter.dm_channel
        Embed = discord.Embed(title=f"Error",
                              description="Sorry this Server doesnt have a delivery channel yet, "
                                          "I will notify the Server Owner for you if I'm able.")
        try:
            await dm_channel.send(embed=Embed)
        except discord.Forbidden:
            if interaction_for_modal is not None:
                await interaction_for_modal.channel.send(
                    "@Reporter, you have turned off the ability to let me DM you. I will notify the "
                    "Server Owner that they haven't created a delivery channel yet.")


def setup(bot):
    log.info("[Cog] AnonModal Report")
    bot.add_cog(AnonModal(bot))
