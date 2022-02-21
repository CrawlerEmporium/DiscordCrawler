import typing
from datetime import datetime, timedelta

import discord

import utils.globals as GG

from discord.ext import commands

from cogsAdmin.models.case import Case, getCaseEmbed, getCaseTargetEmbed, getModDecisionEmbed
from cogsAdmin.models.caseStatus import CaseStatus
from cogsAdmin.models.caseType import CaseType
from crawler_utilities.handlers import logger

from crawler_utilities.utils.functions import get_next_num

log = logger.logger


class TimeOut(discord.ui.Select):
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
            timeoutActual = datetime.now() - timedelta(hours=1)
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


            print(timeoutActual)
            print(self.message)
            await self.member.timeout(timeoutActual, self.message)

            await interaction.response.send_message(f"{self.member} was timed-out for {self.values[0]}")

            await interaction.message.delete()

            case = Case(self.caseId, CaseType.MUTE, CaseStatus.OPEN, self.message, datetime.now(), self.member.id, self.author.id)
            await GG.MDB.cases.insert_one(case.to_dict())
            await GG.MDB.members.update_one({"server": interaction.guild_id, "user": self.member.id}, {"$set": self.memberDB}, upsert=True)
            embed = await getCaseEmbed(self.ctx, case)
            await self.ctx.send(embed=embed)

            decisionChannelExist = await GG.MDB['channelinfo'].find_one({"guild": interaction.guild_id, "type": "MODDECISION"})
            if decisionChannelExist is not None:
                modDecisionChannel = await self.bot.fetch_channel(decisionChannelExist['channel'])
                embed = await getModDecisionEmbed(self.ctx, case)
                await modDecisionChannel.send(embed=embed)

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

        self.add_item(TimeOut(member, message, author, caseId, memberDB, bot, ctx))


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def timeoutCommand(self, ctx, member: typing.Optional[discord.Member], *, message):
        await muteMember(self.bot, ctx, member, message)

    @commands.command()
    @commands.guild_only()
    @GG.is_staff()
    async def untimeoutCommand(self, ctx, member: typing.Optional[discord.Member]):
        await unmuteMember(member)
        await ctx.send(f"Removed timeout for {member}")


async def muteMember(bot, ctx, member: typing.Optional[discord.Member], message):
    if member is None:
        return await ctx.send(
            "Member wasn't found.\n\nCheck the ID, it might not be a member.\nAlso you can't mute someone who isn't on the server.")

    memberDB = await GG.MDB.members.find_one({"server": ctx.guild.id, "user": member.id})
    caseId = await get_next_num(bot.mdb['properties'], 'caseId')

    if memberDB is None:
        memberDB = {"server": ctx.guild.id, "user": member.id, "caseIds": [caseId]}
    else:
        memberDB['caseIds'].append(caseId)

    await ctx.send(f"How long does {member} need to be timed-out?", view=TimeOutView(member, message, ctx.message.author, caseId, memberDB, bot, ctx))


async def unmuteMember(member: typing.Optional[discord.Member]):
    memberExist = await GG.MDB.members.find_one({"server": member.guild.id, "user": member.id})
    if memberExist is not None:
        await member.remove_timeout()
        caseIds = memberExist['caseIds']
        cases = await GG.MDB.cases.find({"caseId": {"$in": caseIds}}).to_list(length=None)
        if cases is not None:
            for case in cases:
                if case['caseType'] == 2:
                    case['status'] = 1
                    await GG.MDB.cases.update_one({"caseId": case['caseId']}, {"$set": {"status": 1}})


def setup(bot):
    log.info("[Admin] Timeout")
    bot.add_cog(Mute(bot))
