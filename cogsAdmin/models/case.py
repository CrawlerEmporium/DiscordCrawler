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
    await ctx.guild.chunk()
    moderator = await ctx.guild.fetch_member(case.mod)
    target = await ctx.guild.fetch_member(case.target)

    if case.caseType == CaseType.NOTE:
        embed.colour = Colour.blue()
        embed.title = f"Note"

    elif case.caseType == CaseType.WARNING:
        embed.colour = Colour.gold()
        embed.title = f"Warning"

    elif case.caseType == CaseType.KICK:
        embed.colour = Colour.orange()
        embed.title = f"Kick"

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
    await ctx.guild.chunk()
    moderator = await ctx.guild.fetch_member(case.mod)

    embed.title = "You have been "
    embed.description = f"The following message as included:\n\n``{case.message}``\n\n"
    if case.caseType == CaseType.WARNING:
        embed.colour = Colour.gold()
        embed.title = f"Warned on"
        embed.description += "Warnings don't mean the end of the world. They are used to track potential rule-breakers and to keep record for the complete staff team."

    elif case.caseType == CaseType.KICK:
        embed.colour = Colour.orange()
        embed.title = f"Kicked from"
        embed.description += "You can always rejoin the server, all your prior warnings will **not** be reset. The next time you break a rule will get you temp-banned or even flat-out banned."

    elif case.caseType == CaseType.TEMPBAN:
        embed.colour = Colour.dark_orange()
        embed.title = f"Temp-banned from"
        embed.description += "You have been temporary banned from the server. Try rejoining in a couple of days, otherwise contact someone from staff and include the case number below in your message."

    elif case.caseType == CaseType.BAN:
        embed.colour = Colour.red()
        embed.title = f"Banned from"
        embed.description += "You have been permanently banned from the server. If you think this is a mistake, contact someone from staff and include the case number below in your message."

    embed.title += f" {ctx.guild.name}"
    embed.set_footer(text=f"Case ID: {case.caseId} - Added by {moderator.display_name}")
    embed.timestamp = case.date
    return embed
