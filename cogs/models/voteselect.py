import discord
from discord.ui import Select, View

from models.poll import Poll
from utils import globals as GG


def create_options(options):
    option_list = []
    for option in options:
        option_list.append(discord.SelectOption(
            label=f"{option.name}", value=f"{option.id}", description=f"{option.name}"
        ))
    return option_list


class VoteSelect(Select):
    def __init__(self, bot: discord.Bot, poll: Poll):
        self.bot = bot
        self.poll = poll

        options = create_options(self.poll.options)

        super().__init__(placeholder="Select the option you want to vote for", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        author_id = interaction.user.id
        message = await self.poll.vote(author_id, selected_option)
        self.disabled = True
        msg = await self.poll.get_message(self.bot)
        await msg.edit(embed=await self.poll.get_embed(self.bot))
        await self.view.message.delete()
        await interaction.response.send_message(
            f"{message}", ephemeral=True
        )


class VoteView(View):
    def __init__(self, bot_: discord.Bot, poll):
        self.bot = bot_
        self.poll = poll
        super().__init__()

        self.add_item(VoteSelect(self.bot, poll))