import typing
import discord
from discord.ext import commands
import utils.globals as GG
from utils import logger

log = logger.logger


class Permission(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def permissionCheck(self, ctx):
        mm = ctx.guild.me.guild_permissions.manage_messages
        mw = ctx.guild.me.guild_permissions.manage_webhooks
        af = ctx.guild.me.guild_permissions.attach_files
        ar = ctx.guild.me.guild_permissions.add_reactions

        em = GG.EmbedWithAuthor(ctx)
        em.title = "Permissions"
        if mm:
            em.add_field(name="Manage_Message", value=f"{mm}")
        else:
            em.add_field(name="Manage_Message", value=f"You should really give me this permission, as it's a mandatory permission. I will have noted this to my owner.")
        em.add_field(name="Manage_Webhooks", value=f"{mw}")
        em.add_field(name="Attach_Files", value=f"{af}")
        em.add_field(name="Add_Reactions", value=f"{ar}")

        await ctx.send(embed=em)

    @commands.command()
    @commands.is_owner()
    async def permissionCheckInChannel(self, ctx):
        mm = ctx.guild.me.permissions_in(ctx.channel).manage_messages
        mw = ctx.guild.me.permissions_in(ctx.channel).manage_webhooks
        af = ctx.guild.me.permissions_in(ctx.channel).attach_files
        ar = ctx.guild.me.permissions_in(ctx.channel).add_reactions

        em = GG.EmbedWithAuthor(ctx)
        em.title = "Permissions"
        if mm:
            em.add_field(name="Manage_Message", value=f"{mm}")
        else:
            em.add_field(name="Manage_Message", value=f"You should really give me this permission, as it's a mandatory permission. I will have noted this to my owner.")
        em.add_field(name="Manage_Webhooks", value=f"{mw}")
        em.add_field(name="Attach_Files", value=f"{af}")
        em.add_field(name="Add_Reactions", value=f"{ar}")

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Permission(bot))
