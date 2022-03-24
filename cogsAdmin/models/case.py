from datetime import datetime

import discord
from discord import Colour

from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType


class Case:
    def __init__(self, caseId: int, caseType: CaseType, status: CaseStatus, message: str, date: datetime, target: int, mod: int):
        self.caseId = caseId
        self.caseType = caseType
        self.status = status
        self.message = message
        self.date = date
        self.target = target
        self.mod = mod

    @classmethod
    def from_data(cls, data):
        return cls(data['caseId'], data['caseType'], data['status'], data['message'], data['date'], data['target'], data['mod'])

    def to_dict(self):
        return {
            'caseId': self.caseId,
            'caseType': self.caseType,
            'status': self.status,
            'message': self.message,
            'date': self.date,
            'target': self.target,
            'mod': self.mod
        }


async def getCaseEmbed(ctx, case: Case):
    embed = discord.Embed()
    await ctx.interaction.guild.chunk()
    moderator = await ctx.interaction.guild.fetch_member(case.mod)
    target = await ctx.interaction.guild.fetch_member(case.target)

    if case.caseType == CaseType.NOTE:
        embed.colour = Colour.blue()
        embed.title = f"Note"

    elif case.caseType == CaseType.WARNING:
        embed.colour = Colour.gold()
        embed.title = f"Warning"

    elif case.caseType == CaseType.MUTE:
        embed.colour = Colour.dark_gray()
        embed.title = f"Time-out"

    elif case.caseType == CaseType.TEMPBAN:
        embed.colour = Colour.dark_orange()
        embed.title = f"Temp-ban"

    elif case.caseType == CaseType.BAN:
        embed.colour = Colour.red()
        embed.title = f"Ban"

    embed.title += f" added for {target.display_name}"
    embed.description = case.message
    embed.set_footer(text=f"Case ID: {case.caseId} - Added by {moderator.display_name}")
    embed.timestamp = case.date
    return embed


async def getCaseTargetEmbed(ctx, case: Case):
    embed = discord.Embed()
    await ctx.interaction.guild.chunk()
    moderator = await ctx.interaction.guild.fetch_member(case.mod)

    pretitle = "You have been "
    embed.description = f"The following message was included:\n\n``{case.message}``\n\n"
    if case.caseType == CaseType.WARNING:
        embed.colour = Colour.gold()
        embed.title = f"{pretitle} Warned on"
        embed.description += "Warnings don't mean the end of the world. They are used to track potential rule-breakers and to keep record for the complete staff team."

    elif case.caseType == CaseType.MUTE:
        embed.colour = Colour.dark_gray()
        embed.title = f"{pretitle} Timed-out on"
        embed.description += "You have been Timed-out. This means you can still read chat, but not participate with it. The next time you break a rule will get you Timed-out for even longer, temp-banned or even flat-out banned."

    elif case.caseType == CaseType.TEMPBAN:
        embed.colour = Colour.dark_orange()
        embed.title = f"{pretitle} Temp-banned from"
        embed.description += "You have been temporary banned from the server. Try rejoining in a couple of days, otherwise contact someone from staff and include the case number below in your message."

    elif case.caseType == CaseType.BAN:
        embed.colour = Colour.red()
        embed.title = f"{pretitle} Banned from"
        embed.description += "You have been permanently banned from the server. If you think this is a mistake, contact someone from staff and include the case number below in your message."

    embed.title = f"{embed.title} {ctx.interaction.guild.name}"
    embed.set_footer(text=f"Case ID: {case.caseId} - Added by {moderator.display_name}")
    embed.timestamp = case.date
    return embed


async def getModDecisionEmbed(ctx, case: Case):
    embed = discord.Embed()
    await ctx.interaction.guild.chunk()
    moderator = await ctx.interaction.guild.fetch_member(case.mod)
    target = await ctx.interaction.guild.fetch_member(case.target)

    pretitle = f"{target} has been"
    if case.caseType == CaseType.WARNING:
        embed.colour = Colour.gold()
        embed.title = f"{pretitle} Warned on"
        embed.description = "Warnings don't mean the end of the world.\nThey are used to track potential rule-breakers and to keep record for the complete staff team."

    elif case.caseType == CaseType.MUTE:
        embed.colour = Colour.dark_gray()
        embed.title = f"{pretitle} Timed-out on"
        embed.description = "People who are Timed-out are rowdy and/or multiple rule breakers (either multiple rules at once, or the same rule more than once).\nThey will still be able to read chat, but can't interact with it."

    elif case.caseType == CaseType.TEMPBAN:
        embed.colour = Colour.dark_orange()
        embed.title = f"{pretitle} Temp-banned from"
        embed.description = f"{target.mention} has been temporary banned from the server.\nThey can rejoin in a couple of days. If you think this is a mistake, contact someone from staff and include the case number below in your message."

    elif case.caseType == CaseType.BAN:
        embed.colour = Colour.red()
        embed.title = f"{pretitle} Banned from"
        embed.description = f"{target.mention} has been permanently banned from the server. If you think this is a mistake, contact someone from staff and include the case number below in your message."

    embed.title = f"{embed.title} {ctx.interaction.guild.name}"
    embed.set_footer(text=f"Case ID: {case.caseId} - Added by {moderator.display_name}")
    embed.timestamp = case.date
    return embed
