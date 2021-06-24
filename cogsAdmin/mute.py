import typing
from datetime import datetime

import discord

import utils.globals as GG

from discord.ext import commands
from discord.colour import Colour

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from crawler_utilities.utils import logger
from utils.functions import get_next_case_num

log = logger.logger


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # re-apply muted role to user on rejoining of a server if the muted status isn't closed.
    @commands.Cog.listener()
    async def on_member_join(self, member):
        memberExist = await GG.MDB.members.find_one({"server": member.guild.id, "user": member.id})
        if memberExist is not None:
            caseIds = memberExist['caseIds']
            cases = await GG.MDB.cases.find({"caseId": {"$in": caseIds}}).to_list(length=None)
            if cases is not None:
                for case in cases:
                    if case['caseType'] == 2 and case['status'] == 0:
                        roles = await member.guild.fetch_roles()
                        for role in roles:
                            if role.name == "Muted":
                                await member.add_roles(role)
                                continue

    # DiscordPyCommands

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def mute(self, ctx, member: typing.Optional[discord.Member], *, message):
        await muteMember(self.bot, ctx, member, message)

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def unmute(self, ctx, member: typing.Optional[discord.Member]):
        await unmuteMember(ctx, member)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def checkMuteChannels(self, ctx):
        await addMutedToChannels(ctx)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def checkMute(self, ctx):
        await checkMutedRole(ctx)

    # SlashCommands

    # @cog_ext.cog_slash(name="mute", description="Mutes an user.", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="user", description="The user you want to mute.", option_type=6, required=True),
    #     create_option(name="reason", description="The reason for muting this person.", option_type=3, required=True)
    # ])
    # @GG.is_staff()
    # async def muteSlash(self, ctx, member: typing.Optional[discord.Member], *, message):
    #     await muteMember(self.bot, ctx, member, message)
    #
    # @cog_ext.cog_slash(name="unmute", description="Unmutes an user.", guild_ids=GG.slashGuilds, options=[
    #     create_option(name="user", description="The user id of the person you want to mute.", option_type=6,
    #                   required=True)
    # ])
    # @GG.is_staff()
    # async def unmuteSlash(self, ctx, member: typing.Optional[discord.Member]):
    #     await unmuteMember(ctx, member)


async def muteMember(bot, ctx, member: typing.Optional[discord.Member], message):
    if member is None:
        return await ctx.send(
            "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't mute someone who isn't on the server.")

    await checkMutedRole(ctx)
    await addMutedToChannels(ctx)

    memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member.id})
    caseId = await get_next_case_num()

    if memberDB is None:
        memberDB = {"server": ctx.guild.id, "user": member.id, "caseIds": [caseId]}
    else:
        memberDB['caseIds'].append(caseId)

    muted = False
    roles = await ctx.guild.fetch_roles()
    for role in roles:
        if role.name == "Muted":
            muted = True
            await member.add_roles(role)
            continue

    if muted:
        case = Case(caseId, CaseType.MUTE, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.author.id)
        await GG.MDB.cases.insert_one(case.to_dict())
        await GG.MDB.members.update_one({"server": ctx.guild.id, "user": member.id}, {"$set": memberDB},
                                        upsert=True)
        embed = await getCaseEmbed(ctx, case)
        await ctx.send(embed=embed)

        decisionChannelExist = await GG.MDB['channelinfo'].find_one(
            {"guild": ctx.message.guild.id, "type": "MODDECISION"})
        if decisionChannelExist is not None:
            modDecisionChannel = await bot.fetch_channel(decisionChannelExist['channel'])
            embed = await getModDecisionEmbed(ctx, case)
            await modDecisionChannel.send(embed=embed)

        if member.dm_channel is not None:
            DM = member.dm_channel
        else:
            DM = await member.create_dm()

        try:
            embed = await getCaseTargetEmbed(ctx, case)
            await DM.send(embed=embed)
            await ctx.send(f"DM with info send to {member}")
        except discord.Forbidden:
            await ctx.send(f"Message failed to send. (Not allowed to DM)")
    else:
        await ctx.send(
            "Couldn't find the muted role, or something else went wrong. Please check if I have the proper permissions.")


async def unmuteMember(ctx, member: typing.Optional[discord.Member]):
    muted = False
    roles = await ctx.guild.fetch_roles()
    for role in roles:
        if role.name == "Muted":
            muted = True
            await member.remove_roles(role)
            await ctx.send(f"{member.mention} was unmuted.")
            continue
    memberExist = await GG.MDB.members.find_one({"server": member.guild.id, "user": member.id})
    if memberExist is not None:
        caseIds = memberExist['caseIds']
        cases = await GG.MDB.cases.find({"caseId": {"$in": caseIds}}).to_list(length=None)
        if cases is not None:
            for case in cases:
                if case['caseType'] == 2:
                    case['status'] = 1
                    await GG.MDB.cases.update_one({"caseId": case['caseId']}, {"$set": {"status": 1}})
    if not muted:
        await ctx.send(f"Couldn't unmuted {member.mention}. Please check if I have the proper permissions.")


async def checkMutedRole(ctx):
    roles = await ctx.guild.fetch_roles()
    hasRole = False
    for role in roles:
        if role.name == "Muted":
            hasRole = True
            continue

    if not hasRole:
        try:
            await ctx.guild.create_role(name="Muted", colour=Colour.dark_gray(),
                                        reason="Added Muted role, because a mute command was triggered and the role didn't exist yet.")
        except:
            return await ctx.send("Error while creating Muted role, check if I have the ``manage_roles`` permission.")

        await ctx.send("Muted role was created. Please put this role above the roles that have writing permissions.")
    else:
        await ctx.send("I already have found a role named Muted.")


async def addMutedToChannels(ctx):
    roles = await ctx.guild.fetch_roles()
    muted = None
    count = 0
    for role in roles:
        if role.name == "Muted":
            muted = role
            continue

    if muted is not None:
        channels = await ctx.guild.fetch_channels()
        for channel in channels:
            if type(channel) == discord.TextChannel:
                if channel.overwrites_for(muted).pair()[0].value == 0 and channel.overwrites_for(muted).pair()[
                    1].value == 0:
                    try:
                        await channel.set_permissions(muted, send_messages=False)
                        count += 1
                    except:
                        await ctx.send(
                            f"Something went wrong while overwriting permissions to {channel}, check if I have the ``manage_roles`` permission.")
                if channel.overwrites_for(muted).pair()[0].value == 2048 and channel.overwrites_for(muted).pair()[
                    1].value == 0:
                    await ctx.send(
                        f"While checking permissions, I found that the {channel.mention} channel has 'send_messages' enabled for the muted role. I won't touch it, as this might be on purpose.")

        await ctx.send(f"Added muted overwrite to {count} channel(s).")


def setup(bot):
    log.info("[Admin] Mute")
    bot.add_cog(Mute(bot))
