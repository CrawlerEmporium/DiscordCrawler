import csv
import io

import discord

from cogs.models.voteselect import VoteView
from crawler_utilities.cogs.localization import get_command_kwargs, get_parameter_kwargs
from discord import SlashCommandGroup, Option, AutocompleteContext, File
from discord.ext import commands
from utils import globals as GG
from crawler_utilities.utils.functions import get_next_num
from models.poll import Poll, PollOption, PollSetting

log = GG.log


def get_poll_options(content):
    loopTime = 0
    options = []
    for _ in content:
        # get from } [option 1]
        # if newThis == -1:
        stillOptions = content.find("[")
        if stillOptions != -1:
            if loopTime == 0:
                first = content.find("[") + 1
                second = content.find("]")
                second1 = second + 1
                options.append(content[first:second])
                loopTime += 1
            else:
                content = content[second1:]
                first = content.find("[") + 1
                second = content.find("]")
                second1 = second + 1
                options.append(content[first:second])
                loopTime += 1
    return options


async def get_open_polls(ctx: AutocompleteContext):
    if ctx.interaction.user.guild_permissions.manage_messages:
        db = await GG.MDB['polls'].find({"server_id": ctx.interaction.guild_id, "status": True}).to_list(length=None)
    else:
        db = await GG.MDB['polls'].find({"server_id": ctx.interaction.guild_id, "status": True, "admin": False}).to_list(length=None)
    return [f"{poll['id']} - {poll['title']}" for poll in db]


async def get_all_polls(ctx: AutocompleteContext):
    db = await GG.MDB['polls'].find({"server_id": ctx.interaction.guild_id}).to_list(length=None)
    return [f"{poll['id']} - {poll['title']}" for poll in db]


async def current_available_settings(ctx: AutocompleteContext):
    return ['locked', 'anonymous']


class Poller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cogName = 'poll'
    poll = SlashCommandGroup(name="poll", description="Create polls for your server")

    @poll.command(**get_command_kwargs(cogName, "create"))
    @commands.guild_only()
    async def create(self,
                     ctx,
                     title: Option(str, **get_parameter_kwargs(cogName, "create.title")),
                     options: Option(str, **get_parameter_kwargs(cogName, "create.options")),
                     locked: Option(bool, **get_parameter_kwargs(cogName, "create.locked"), required=False, default=False),
                     anonymous: Option(bool, **get_parameter_kwargs(cogName, "create.anonymous"), required=False, default=False),
                     multivote: Option(int, **get_parameter_kwargs(cogName, "create.multivote"), required=False, default=1),
                     autolock: Option(int, **get_parameter_kwargs(cogName, "create.autolock"), required=False, default=0)):
        separated_options = get_poll_options(options)
        if 1 > len(separated_options) or len(separated_options) > 20:
            return await ctx.respond(content='This polling command requires between 2 and 20 options, you either have too many or too little options. Try again.')
        else:
            _id = await get_next_num(self.bot.mdb['properties'], 'pollId')
            options_list = []
            for i in range(len(separated_options) - 1):
                options_list.append(PollOption.new(i, separated_options[i]))
            new_poll = Poll.new(_id, ctx.interaction.user.id, title, options_list, ctx.interaction.guild_id, ctx.channel.id)
            new_poll.populate_settings(locked, anonymous, multivote, autolock)

            await GG.MDB['polls'].insert_one(new_poll.to_dict())
            embed = await new_poll.get_embed(guild=ctx.interaction.guild)
            msg = await ctx.channel.send(content="<@&1009059409894314034>", embed=embed)
            new_poll.message_id = msg.id
            await new_poll.commit()
            return await ctx.respond(f"Poll with title: ``{new_poll.title}`` and id: ``{new_poll.id}`` was succesfully posted", ephemeral=True)

    @poll.command(**get_command_kwargs(cogName, "admin"), guild_ids=[363680385336606740])
    @commands.guild_only()
    async def admin(self, ctx, member: Option(discord.Member, **get_parameter_kwargs(cogName, "admin.member"))):
        _id = await get_next_num(self.bot.mdb['properties'], 'pollId')
        options = ["No action", "Emergency timeout", "DM warning", "In channel warning", "Formal warning", "Timeout", "Kick", "Ban"]
        option_list = []
        for i in range(len(options) - 1):
            option_list.append(PollOption.new(i, options[i]))
        new_poll = Poll.new(_id, ctx.interaction.user.id, f"Moderative Action for <@{member.id}>", option_list, ctx.interaction.guild_id, ctx.channel.id, admin=True)
        new_poll.populate_settings(False, False, 1, 11)
        await GG.MDB['polls'].insert_one(new_poll.to_dict())
        embed = await new_poll.get_embed(guild=ctx.interaction.guild)
        msg = await ctx.channel.send(embed=embed)
        new_poll.message_id = msg.id
        await new_poll.commit()
        return await ctx.respond(f"Poll with title: ``{new_poll.title}`` and id: ``{new_poll.id}`` was succesfully posted", ephemeral=True)

    @poll.command(**get_command_kwargs(cogName, "vote"))
    @commands.guild_only()
    async def vote(self,
                   ctx,
                   id: Option(str, autocomplete=get_open_polls, **get_parameter_kwargs(cogName, "vote.id"))):
        poll = await Poll.from_id(id.split(" - ")[0])
        view = VoteView(bot_=ctx.bot, poll=poll)
        await ctx.respond(f"Voting for ``{poll.title}``", ephemeral=True, view=view)

    @poll.command(**get_command_kwargs(cogName, "close"))
    @commands.guild_only()
    async def close(self,
                    ctx,
                    id: Option(str, autocomplete=get_open_polls, **get_parameter_kwargs(cogName, "close.id"))):
        poll = await Poll.from_id(id.split(" - ")[0])
        if ctx.interaction.user.id == poll.author or ctx.interaction.user.guild_permissions.manage_messages:
            await poll.close()
            msg = await poll.get_message(ctx.bot)
            await msg.edit(embed=await poll.get_embed(ctx.bot))
            return await ctx.respond(f"``{poll.title}`` was closed.")
        else:
            return await ctx.respond("Only the author or a moderator can close a poll.")

    @poll.command(**get_command_kwargs(cogName, "settings"))
    @commands.guild_only()
    async def settings(self,
                       ctx,
                       id: Option(str, autocomplete=get_open_polls, **get_parameter_kwargs(cogName, "settings.id")),
                       setting: Option(str, autocomplete=current_available_settings, **get_parameter_kwargs(cogName, "settings.setting"))):
        poll = await Poll.from_id(id.split(" - ")[0])
        for _set in poll.settings:
            if _set.name == setting:
                _set.toggle_setting()
                await poll.commit()
                return await ctx.respond(f"``{poll.title}``'s {_set.name} setting was set to {_set.state}")
        else:
            return await ctx.respond(f"This setting has not been implemented yet.")

    @poll.command(**get_command_kwargs(cogName, "info"))
    @commands.guild_only()
    async def info(self,
                   ctx,
                   id: Option(str, autocomplete=get_all_polls, **get_parameter_kwargs(cogName, "info.id")),
                   export: Option(bool, **get_parameter_kwargs(cogName, "info.export"), required=False, default=False)):
        poll = await Poll.from_id(id.split(" - ")[0])
        file = None
        if not poll.get_state_by_setting_name("anonymous"):
            if (ctx.interaction.user.id == poll.author or ctx.interaction.user.guild_permissions.manage_messages) and export:
                f = io.StringIO()
                csv.writer(f).writerow(["user_id", "option_id", "option_name"])
                for voter in poll.voters:
                    csv.writer(f).writerow([f"{voter.user_id}", f"{voter.option_id}", f"{poll.get_option_name_by_id(voter.option_id)}"])
                f.seek(0)

                buffer = io.BytesIO()
                buffer.write(f.getvalue().encode())
                buffer.seek(0)

                file = File(buffer, filename=f"Voter export for {poll.title}.csv")

        embed = discord.Embed()
        embed.title = f"Info embed for {poll.title} ({poll.id})"
        embed.description = f"Status: {GG.get_status(poll.status)} - Total Votes: {len(poll.voters)}"
        embed.add_field(name="Locked", value=GG.human_readable_boolean(poll.get_state_by_setting_name("locked")), inline=False)
        embed.add_field(name="Anonymous", value=GG.human_readable_boolean(poll.get_state_by_setting_name("anonymous")), inline=False)
        embed.add_field(name="Multivote", value=f"Castable votes: {poll.get_state_by_setting_name('multivote')}", inline=False)
        autolock = False if poll.get_state_by_setting_name('autolock') == 0 else True
        if autolock:
            embed.add_field(name="Autolock", value=f"Automatically closes after ``{poll.get_state_by_setting_name('autolock')}`` votes", inline=False)
        else:
            embed.add_field(name="Autolock", value=GG.human_readable_boolean(False), inline=False)

        await ctx.respond(embed=embed, file=file, ephemeral=True)


def setup(bot):
    log.info("[Cog] Poller")
    bot.add_cog(Poller(bot))
