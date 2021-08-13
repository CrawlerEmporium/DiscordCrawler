import discord
from discord import ButtonStyle, Interaction
from discord.ui import View


class Greylist(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Reject", style=ButtonStyle.red, custom_id='reject')
    async def reject(self, button, interaction: Interaction):
        msg = interaction.message
        embed = msg.embeds[0]
        msgID = 0
        channelID = 0
        i = 0
        for field in embed.fields:
            if field.name == "MSGID":
                msgID = field.value
                embed.remove_field(i)
            i += 1
        i = 0
        for field in embed.fields:
            if field.name == "CHANNELID":
                channelID = field.value
                embed.remove_field(i)
            i += 1
        try:
            channel = await self.bot.fetch_channel(channelID)
            message = await channel.fetch_message(msgID)
            await message.delete()

            embed.set_footer(text=f"Message was removed by {interaction.user.display_name}.")
            await interaction.response.edit_message(embed=embed, view=None)

        except:
            embed.set_footer(text="Couldn't find message, probably already deleted.")
            await interaction.response.edit_message(embed=embed, view=None)

        self.stop()
