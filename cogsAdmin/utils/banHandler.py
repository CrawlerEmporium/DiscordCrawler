from datetime import datetime

import discord

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType

from utils import globals as GG
from crawler_utilities.utils.functions import get_next_num


async def BanCommand(self, ctx, member, message, automatic=False):
    if member is None:
        return await ctx.send(
            "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't ban someone who isn't on the server.")

    memberDB = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member.id})
    caseId = await get_next_num(self.bot.mdb['properties'], 'caseId')

    if memberDB is None:
        memberDB = {"server": ctx.interaction.guild_id, "user": member.id, "caseIds": [caseId]}
    else:
        memberDB['caseIds'].append(caseId)

    case = Case(caseId, CaseType.BAN, CaseStatus.OPEN, message, datetime.now(), member.id, ctx.interaction.user.id)
    await GG.MDB.cases.insert_one(case.to_dict())
    await GG.MDB.members.update_one({"server": ctx.interaction.guild_id, "user": member.id}, {"$set": memberDB},
                                    upsert=True)
    if not automatic:
        embed = await getCaseEmbed(ctx, case)
        await ctx.respond(embed=embed)

    decisionChannelExist = await GG.MDB['channelinfo'].find_one({"guild": ctx.interaction.guild_id, "type": "MODDECISION"})
    if decisionChannelExist is not None:
        modDecisionChannel = await self.bot.fetch_channel(decisionChannelExist['channel'])
        embed = await getModDecisionEmbed(ctx, case)
        await modDecisionChannel.send(embed=embed)

    if member.dm_channel is not None:
        DM = member.dm_channel
    else:
        DM = await member.create_dm()
    try:
        embed = await getCaseTargetEmbed(ctx, case)
        await DM.send(embed=embed)
        if not automatic:
            await ctx.send(f"DM with info send to {member}")
    except discord.Forbidden:
        if not automatic:
            await ctx.send(f"Message failed to send. (Not allowed to DM)")

    await member.ban(reason=message, delete_message_seconds=604800)


async def HoneypotCommand(bot, guild, member, message):
    memberDB = await GG.MDB.members.find_one({"server": guild.id, "user": member.id})
    caseId = await get_next_num(bot.mdb['properties'], 'caseId')

    if memberDB is None:
        memberDB = {"server": guild.id, "user": member.id, "caseIds": [caseId]}
    else:
        memberDB['caseIds'].append(caseId)

    case = Case(caseId, CaseType.BAN, CaseStatus.OPEN, message, datetime.now(), member.id, GG.BOT)
    await GG.MDB.cases.insert_one(case.to_dict())
    await GG.MDB.members.update_one({"server": guild.id, "user": member.id}, {"$set": memberDB},
                                    upsert=True)

    decisionChannelExist = await GG.MDB['channelinfo'].find_one(
        {"guild": guild.id, "type": "MODDECISION"})
    if decisionChannelExist is not None:
        modDecisionChannel = await bot.fetch_channel(decisionChannelExist['channel'])
        embed = await getModDecisionEmbed(None, case, guild, "Winnie the Pooh")
        await modDecisionChannel.send(embed=embed)

    if member.dm_channel is not None:
        DM = member.dm_channel
    else:
        DM = await member.create_dm()
    try:
        embed = await getCaseTargetEmbed(None, case, guild, "Winnie the Pooh")
        await DM.send(embed=embed)
    except discord.Forbidden:
        pass

    await member.ban(reason=message, delete_message_seconds=604800)
