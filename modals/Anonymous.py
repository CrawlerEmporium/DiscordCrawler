import discord
from discord import InputTextStyle, Interaction
from discord.ui import Modal, InputText
from utils import globals as GG
from cryptography.fernet import Fernet
from datetime import datetime

log = GG.log


class Anonymous(Modal):
    def __init__(self, bot, interaction, author, delivery_channel) -> None:
        super().__init__(title="Anonymous Report")

        self.bot = bot
        self.interaction = interaction
        self.author = author
        self.delivery_channel = delivery_channel

        self.add_item(InputText(label="Information", placeholder="What do you want to report to/share with the staff?",
                                required=True, style=InputTextStyle.long))
        self.add_item(InputText(label="Optional Links", placeholder="Insert links (if any) here", required=False,
                                style=InputTextStyle.long))
        self.add_item(InputText(label="Public or Anonymous?",
                                placeholder="Put ANY text in here, and you will be thrown into a private channel with staff.",
                                required=False, style=InputTextStyle.long))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"New report", description=self.children[0].value)
        if self.children[1].value != "":
            embed.add_field(name="Optional Links", value=self.children[1].value)

        if self.children[2].value != "":
            await self.createPrivateChannel(interaction, embed)
        else:
            await self.createAnonymousPost(interaction, embed)

    async def createPrivateChannel(self, interaction, embed):

        thread = await self.delivery_channel.create_thread(name=f"[{datetime.now().date()}] - [{self.author}]",
                                                           reason="Anonymous public request triggered.")
        await thread.send(embed=embed)
        user = self.bot.get_user(self.author.id)
        await thread.add_user(user)

        await interaction.followup.send(
            f"A private channel was created for you. You can find it here: {thread.jump_url}", ephemeral=True)

    async def createAnonymousPost(self, interaction, embed):
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
            await interaction.followup.send(
                f"Sorry, something went wrong while posting your report, please try again at a later stage.\n"
                f"Or try contacting someone from staff directly, your name will not be shared with anyone else.",
                ephemeral=True)
