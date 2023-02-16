import discord

from crawler_utilities.handlers.errors import CrawlerException

from utils import globals as GG


class Poll:
    def __init__(self, id: int, author: int, title: str, options: list, server_id: int, channel_id: int, message_id: int = 0, locked: bool = False, voters: list = None, status: bool = True):
        if voters is None:
            voters = []
        self.id = id
        self.author = author
        self.title = title
        self.options = options
        self.server_id = server_id
        self.locked = locked
        self.voters = voters
        self.status = status
        self.channel_id = channel_id
        self.message_id = message_id

    @classmethod
    def new(cls, id, author, title, options, server_id, channel_id, message_id=None, locked=False):
        return cls(id, author, title, options, server_id, channel_id, message_id, locked, voters=None, status=True)

    @classmethod
    def from_dict(cls, poll_dict):
        poll_dict['options'] = [PollOption.from_dict(o) for o in poll_dict['options']]
        poll_dict['voters'] = [Voter.from_dict(v) for v in poll_dict['voters']]
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

    async def vote(self, author, option_id):
        option = self.get_option_by_id(option_id)
        for votes in self.voters:
            if votes.user_id == author and not self.status:
                return "You cannot vote anymore, this poll is closed."
            elif votes.user_id == author and self.locked:
                return "You cannot change your vote, as this poll is locked."
            elif votes.user_id == author:
                votes.option_id = option.id
                await self.commit()
                return f"You have changed your vote to ``{option.name}`` in ``{self.title}``"

        self.voters.append(Voter(author, option.id))
        await self.commit()
        return f"You have voted for ``{option.name}`` in ``{self.title}``"

    async def get_message(self, bot):
        msg = await bot.get_channel(self.channel_id).fetch_message(self.message_id)
        return msg

    async def commit(self):
        await GG.MDB['polls'].replace_one({"id": self.id}, self.to_dict(), upsert=True)

    async def get_embed(self, bot=None, guild=None):
        if bot is None and guild is None:
            return discord.Embed(title="No bot or guild found")
        embed = discord.Embed()
        embed.title = f"{self.title}"
        embed.colour = 0x6596c7
        embed.set_footer(text=f"Poll Id: {self.id} - Total Votes: {len(self.voters)} - Status: {GG.get_status(self.status)}")
        if guild is None and bot is not None:
            guild = await bot.fetch_guild(self.server_id)
        winning_option = ""
        option_votes = 0
        total_votes = 0
        other_options = []
        for option in self.options:
            voters = [v.user_id for v in self.voters if v.option_id == option.id]
            total_votes += len(voters)
            if len(voters) > option_votes:
                option_votes = len(voters)
                winning_option = option.name
            voter_string = ""
            if len(voters) == 0:
                voter_string = "- No votes yet"
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
            embed.description = f"The winner of this poll is ``{winning_option}`` with {option_votes} out of {total_votes} votes.\n\nVote Results:{''.join(other_options)}"
        return embed

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "title": self.title,
            "options": [o.to_dict() for o in self.options],
            "server_id": self.server_id,
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "locked": self.locked,
            "voters": [v.to_dict() for v in self.voters],
            "status": self.status
        }


class Voter:
    def __init__(self, user_id: int, option_id: int):
        self.user_id = user_id
        self.option_id = option_id

    @classmethod
    def new(cls, user_id, option_id):
        return cls(user_id, option_id)

    @classmethod
    def from_dict(cls, voter):
        return cls(**voter)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "option_id": self.option_id
        }


class PollOption:
    def __init__(self, id: int, name: int):
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


class PollException(CrawlerException):
    pass
