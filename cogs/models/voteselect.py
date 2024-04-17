import discord
from discord import SelectOption
from discord.ui import Select, View

from models.poll import Poll


def create_options(options):
    option_list = []
    for option in options:
        option_list.append(SelectOption(
            label=f"{option.name}", value=f"{option.id}"
        ))
    return option_list


class VoteSelect(Select):
    def __init__(self, bot: discord.Bot, poll_id, options, multivote):
        self.bot = bot
        self.poll_id = poll_id
        self.multivote = multivote

        options = create_options(options)
        if multivote > 1:
            placeholder = f"Select up to {multivote} options you want to vote for"
        else:
            placeholder = "Select the option you want to vote for"

        super().__init__(placeholder=placeholder, min_values=1, max_values=multivote, options=options)

    async def callback(self, interaction: discord.Interaction):
        poll = await Poll.from_id(self.poll_id)
        author_id = interaction.user.id
        if len(self.values) > 1:
            message = await poll.vote(author_id, True, self.values)
        else:
            message = await poll.vote(author_id, False, self.values[0])
        self.disabled = True
        msg = await poll.get_message(self.bot)
        await msg.edit(embed=await poll.get_embed(self.bot))
        try:
            await self.view.message.delete()
        except:
            pass
        await interaction.response.send_message(
            f"{message}", ephemeral=True
        )


class VoteView(View):
    def __init__(self, bot_: discord.Bot, poll_id, options, multivote):
        self.bot = bot_
        self.poll_id = poll_id
        self.options = options
        self.multivote = multivote
        super().__init__()

        self.add_item(VoteSelect(self.bot, poll_id, options, multivote))
