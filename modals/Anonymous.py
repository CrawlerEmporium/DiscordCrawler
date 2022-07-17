import discord
from discord import InputTextStyle, Interaction
from discord.ui import Modal, InputText
from utils import globals as GG
from cryptography.fernet import Fernet

log = GG.log


class Anonymous(Modal):
    def __init__(self, bot, interaction, author, delivery_channel) -> None:
        super().__init__(title="Anonymous Report")

        self.bot = bot
        self.interaction = interaction
        self.author = author
        self.delivery_channel = delivery_channel

        self.add_item(InputText(label="Information", placeholder="What do you want to report to/share with the staff?", required=True, style=InputTextStyle.long))
        self.add_item(InputText(label="Optional Links", placeholder="Insert links (if any) here", required=False, style=InputTextStyle.long))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"New report", description=self.children[0].value)
        if self.children[1].value != "":
            embed.add_field(name="Optional Links", value=self.children[1].value)
        message = await self.delivery_channel.send(embed=embed)

        if message is not None:
            embed.set_footer(text=f"Reply to this report by using • !reply {message.id} <your reply>")
            await message.edit(embed=embed)
            hashAuthor = f"{self.author.id}".encode()
            f = Fernet(GG.KEY)
            encrypt = f.encrypt(hashAuthor)
            await GG.MDB['reports'].insert_one({"user": encrypt, "message": message.id})

            await interaction.followup.send(f"Your report was successfully delivered to the staff!", ephemeral=True)
        else:
            await interaction.followup.send(f"Sorry, something went wrong while posting your report, please try again at a later stage.\n"
                                            f"Or try contacting someone from staff directly, your name will not be shared with anyone else.", ephemeral=True)
