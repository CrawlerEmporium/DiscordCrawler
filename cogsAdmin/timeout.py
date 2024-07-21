import typing
from datetime import datetime, timedelta

import discord
from discord import slash_command, Option

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from utils import globals as GG

from crawler_utilities.utils.functions import get_next_num
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs

log = GG.log


class TimeOutSelection(discord.ui.Select):
    def __init__(self, cmember, cmessage, cauthor, caseId, memberDB, bot, ctx):
        self.member = cmember
        self.author = cauthor
        self.message = cmessage
        self.caseId = caseId
        self.memberDB = memberDB
        self.bot = bot
        self.ctx = ctx

        options = [
            discord.SelectOption(
                label="10 Minutes"
            ),
            discord.SelectOption(
                label="1 Hour"
            ),
            discord.SelectOption(
                label="3 Hours"
            ),
            discord.SelectOption(
                label="6 Hours"
            ),
            discord.SelectOption(
                label="12 Hours"
            ),
            discord.SelectOption(
                label="1 Day"
            ),
            discord.SelectOption(
                label="3 Days"
            ),
            discord.SelectOption(
                label="1 Week"
            ),
        ]

        super().__init__(
            placeholder="Choose the time-outs duration...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.author != interaction.user:
            return
        else:
            timeoutActual = datetime.now() - timedelta(hours=2)
            if self.values[0] == "10 Minutes":
                timeoutActual = timeoutActual + timedelta(minutes=10)
            elif self.values[0] == "1 Hour":
                timeoutActual = timeoutActual + timedelta(hours=1)
            elif self.values[0] == "3 Hours":
                timeoutActual = timeoutActual + timedelta(hours=3)
            elif self.values[0] == "6 Hours":
                timeoutActual = timeoutActual + timedelta(hours=6)
            elif self.values[0] == "12 Hours":
                timeoutActual = timeoutActual + timedelta(hours=12)
            elif self.values[0] == "1 Day":
                timeoutActual = timeoutActual + timedelta(days=1)
            elif self.values[0] == "3 Days":
                timeoutActual = timeoutActual + timedelta(days=3)
            elif self.values[0] == "1 Week":
                timeoutActual = timeoutActual + timedelta(weeks=1)
            else:
                timeoutActual = timeoutActual

            await self.member.timeout(until=timeoutActual, reason=self.message)

            await interaction.response.send_message(f"{self.member} was timed-out for {self.values[0]}")

            await interaction.message.delete()

            case = Case(self.caseId, CaseType.MUTE, CaseStatus.OPEN, self.message, datetime.now(), self.member.id, self.author.id)
            await GG.MDB.cases.insert_one(case.to_dict())
            await GG.MDB.members.update_one({"server": interaction.guild_id, "user": self.member.id}, {"$set": self.memberDB}, upsert=True)
            embed = await getCaseEmbed(self.ctx, case)
            await self.ctx.send(embed=embed)

            if self.member.dm_channel is not None:
                DM = self.member.dm_channel
            else:
                DM = await self.member.create_dm()

            try:
                embed = await getCaseTargetEmbed(self.ctx, case)
                await DM.send(embed=embed)
                await self.ctx.send(f"DM with info send to {self.member}")
            except discord.Forbidden:
                await self.ctx.send(f"Message failed to send. (Not allowed to DM)")


class TimeOutView(discord.ui.View):
    def __init__(self, member, message, author, caseId, memberDB, bot, ctx):
        super().__init__()

        self.add_item(TimeOutSelection(member, message, author, caseId, memberDB, bot, ctx))


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = "timeout"

    @slash_command(**get_command_kwargs(cogName, "timeout"))
    @commands.guild_only()
    async def timeout(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, "timeout.member")), message: Option(str, **get_parameter_kwargs(cogName, "timeout.message"))):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await muteMember(self.bot, ctx, member, message)

    @slash_command(**get_command_kwargs(cogName, "untimeout"))
    @commands.guild_only()
    async def untimeout(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, "untimeout.member"))):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_bool_slash(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)
        await unmuteMember(ctx, member)


async def muteMember(bot, ctx, member: typing.Optional[discord.Member], message):
    memberDB = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member.id})
    caseId = await get_next_num(bot.mdb['properties'], 'caseId')

    if memberDB is None:
        memberDB = {"server": ctx.interaction.guild_id, "user": member.id, "caseIds": [caseId]}
    else:
        memberDB['caseIds'].append(caseId)

    await ctx.respond(f"How long does {member} need to be timed-out?", view=TimeOutView(member, message, ctx.interaction.user, caseId, memberDB, bot, ctx))


async def unmuteMember(ctx, member: typing.Optional[discord.Member]):
    memberExist = await GG.MDB.members.find_one({"server": ctx.interaction.guild_id, "user": member.id})
    if memberExist is not None:
        await member.remove_timeout()
        caseIds = memberExist['caseIds']
        cases = await GG.MDB.cases.find({"caseId": {"$in": caseIds}}).to_list(length=None)
        if cases is not None:
            for case in cases:
                if case['caseType'] == 2:
                    case['status'] = 1
                    await GG.MDB.cases.update_one({"caseId": case['caseId']}, {"$set": {"status": 1}})
        await ctx.respond(f"Removed timeout for {member}")


def setup(bot):
    log.info("[Admin] Timeout")
    bot.add_cog(Timeout(bot))
