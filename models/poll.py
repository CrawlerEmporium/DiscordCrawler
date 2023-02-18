import discord
import uuid

from crawler_utilities.handlers.errors import CrawlerException

from utils import globals as GG


class Poll:
    def __init__(self, id: int, author: int, title: str, options: list, server_id: int, channel_id: int, message_id: int = 0, settings: list = None, voters: list = None, status: bool = True):
        if voters is None:
            voters = []
        if settings is None:
            settings = []
        self.id = id
        self.author = author
        self.title = title
        self.options = options
        self.server_id = server_id
        self.settings = settings
        self.voters = voters
        self.status = status
        self.channel_id = channel_id
        self.message_id = message_id

    @classmethod
    def new(cls, id, author, title, options, server_id, channel_id, message_id=None, settings=None):
        return cls(id, author, title, options, server_id, channel_id, message_id, settings, voters=None, status=True)

    @classmethod
    def from_dict(cls, poll_dict):
        poll_dict['options'] = [PollOption.from_dict(o) for o in poll_dict['options']]
        poll_dict['voters'] = [Voter.from_dict(v) for v in poll_dict['voters']]
        print(len(poll_dict['voters']))
        poll_dict['settings'] = [PollSetting.from_dict(s) for s in poll_dict['settings']]
        return cls(**poll_dict)

    @classmethod
    async def from_id(cls, poll_id):
        db_poll = await GG.MDB['polls'].find_one({"id": poll_id})
        if db_poll is not None:
            del db_poll['_id']
            return cls.from_dict(db_poll)
        else:
            raise PollException(f"Poll with id: {poll_id} cannot be found.")

    def get_option_by_id(self, option_id):
        for option in self.options:
            if int(option.id) == int(option_id):
                return option

    async def close(self):
        self.status = False
        await self.commit()

    def get_state_by_setting_name(self, name):
        return [setting for setting in self.settings if setting.name == name][0].state

    def populate_settings(self, locked, anonymous, multivote, autolock):
        self.settings.append(PollSetting.new("locked", locked))
        self.settings.append(PollSetting.new("anonymous", anonymous))
        self.settings.append(PollSetting.new("multivote", multivote))
        self.settings.append(PollSetting.new("autolock", autolock))

    async def vote(self, author, multivote, options):
        if len([v for v in self.voters if v.user_id == author]) > 1:
            if not self.status:
                return "You cannot vote anymore, this poll is closed."
            elif self.get_state_by_setting_name("locked"):
                return "You cannot change your vote, as this poll is locked."

        not_author = [v for v in self.voters if v.user_id != author]
        self.voters = not_author
        if multivote:
            voted_options = []
            for option in options:
                option = self.get_option_by_id(option)
                self.voters.append(Voter(author, option.id))
                voted_options.append(option.name)
            await self.commit()
            return f"You have voted for ``{', '.join(voted_options)}`` in ``{self.title}``"
        else:
            option = self.get_option_by_id(options)
            self.voters.append(Voter(author, option.id))
            await self.commit()
            return f"You have voted for ``{option.name}`` in ``{self.title}``"

    async def get_message(self, bot):
        msg = await bot.get_channel(self.channel_id).fetch_message(self.message_id)
        return msg

    async def commit(self):
        await GG.MDB['polls'].replace_one({"id": self.id}, self.to_dict(), upsert=True)
        if self.status:
            autolock = self.get_state_by_setting_name("autolock")
            if autolock != 0:
                if len(self.voters) == autolock:
                    await self.close()

    async def get_embed(self, bot=None, guild=None):
        if bot is None and guild is None:
            return discord.Embed(title="No bot or guild found")
        embed = discord.Embed()
        embed.title = f"{self.title}"
        embed.colour = 0x6596c7
        embed.description = f"Status: {GG.get_status(self.status)}"
        setting_string = self.get_setting_string()
        embed.set_footer(text=f"Id: {self.id} | Current Votes: {len(self.voters)}{setting_string}")
        if guild is None and bot is not None:
            guild = await bot.fetch_guild(self.server_id)
        winning_option = []
        option_votes = 0
        total_votes = 0
        other_options = []
        for option in self.options:
            voters = [v.user_id for v in self.voters if v.option_id == option.id]
            total_votes += len(voters)
            if len(voters) >= option_votes:
                option_votes = len(voters)
                winning_option.append(option.name)
            voter_string = ""
            if len(voters) == 0:
                voter_string = "- No votes yet"
            else:
                if self.get_state_by_setting_name("anonymous"):
                    if len(voters) == 1:
                        voter_string = "- 1 vote"
                    else:
                        voter_string = f"- {len(voters)} votes"
                else:
                    amount = 1
                    for voter in voters:
                        if amount <= 4:
                            guildUser = guild.get_member(voter)
                            if guildUser is not None:
                                voter = f"{guildUser.mention}"
                            else:
                                voter = f"<@{voter}>"
                            voter_string += f"- {voter}\n"
                            amount += 1
                        if amount == 5:
                            voter_string += f"- {len(voters) - 4} more votes..."
            if self.status:
                embed.add_field(name=option.name, value=voter_string)
            else:
                other_options.append(f"\n{option.name} - {len(voters)} votes")
        if not self.status:
            if len(winning_option) > 1:
                embed.description = f"The winners of this poll are ``{', '.join(winning_option)}`` with each {option_votes} out of {total_votes} votes.\n\n**Vote Results**:\n{''.join(other_options)}"
            else:
                embed.description = f"The winner of this poll is ``{winning_option[0]}`` with {option_votes} out of {total_votes} votes.\n\n**Vote Results**:\n{''.join(other_options)}"
        return embed

    def get_setting_string(self):
        settings_string = ""
        if self.get_state_by_setting_name("locked"):
            settings_string += " | Locked"
        if self.get_state_by_setting_name("anonymous"):
            settings_string += " | Anonymous"
        multivote = self.get_state_by_setting_name("multivote")
        if multivote > 1:
            settings_string += f" | {multivote} votes"
        autolock = self.get_state_by_setting_name("autolock")
        if autolock > 0:
            settings_string += f" | Locks after {autolock} votes"
        return settings_string

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "title": self.title,
            "options": [o.to_dict() for o in self.options],
            "server_id": self.server_id,
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "settings": [s.to_dict() for s in self.settings],
            "voters": [v.to_dict() for v in self.voters],
            "status": self.status
        }


class Voter:
    def __init__(self, user_id: int, option_id: int, _id: str = str(uuid.uuid4())):
        self.user_id = user_id
        self.option_id = option_id
        self._id = _id

    @classmethod
    def new(cls, user_id, option_id, _id):
        return cls(user_id, option_id, _id)

    @classmethod
    def from_dict(cls, voter):
        return cls(**voter)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "option_id": self.option_id,
            "_id": self._id
        }


class PollOption:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    @classmethod
    def new(cls, id, name):
        return cls(id, name)

    @classmethod
    def from_dict(cls, option):
        return cls(**option)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class PollSetting:
    def __init__(self, name: str, state):
        self.name = name
        self.state = state

    @classmethod
    def new(cls, name, state):
        return cls(name, state)

    @classmethod
    def from_dict(cls, setting):
        return cls(**setting)

    def toggle_setting(self):
        self.state = not self.state

    def to_dict(self):
        return {
            "name": self.name,
            "state": self.state,
        }


class PollException(CrawlerException):
    pass
