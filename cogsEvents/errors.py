import traceback

import asyncio
from random import random

from aiohttp import ClientResponseError, ClientOSError
from discord import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands import CommandInvokeError
from crawler_utilities.handlers.errors import CrawlerException, InvalidArgument, EvaluationError
import utils.globals as GG
from crawler_utilities.utils import logger
from crawler_utilities.utils.functions import discord_trim

log = logger.logger

adj = ['Lonely', 'Unceasing', 'Overused', 'Blue', 'Orange', 'Tiny', 'Giant', 'Deadly', 'Hopeless', 'Unknown',
       'Defeated', 'Deafening', 'Tenacious', 'Evasive', 'Omniscient', 'Wild', 'Toxic', 'Spotless', 'Impossible',
       'Faded', 'Hemorrhaging', 'Godless', 'Judicious', 'Despondent', 'Fatal', 'Serene', 'Blistering', 'Last', 'Dull',
       'Gruesome', 'Azure', 'Blighted', 'Pink', 'Languid', 'Outlawed', 'Penultimate', 'Sundered', 'Hollow', 'Violent',
       'Divine', 'Pious', 'Shattered', 'Shrouded', 'Decaying', 'Defeated', 'Callous', 'Inferior', 'Superior', 'Clear',
       'Veiled', 'Weeping', 'Swift', 'Unceasing', 'Vengeful', 'Lone', 'Cold', 'Hot', 'Purple', 'Brutal', 'Flying',
       'Driving', 'Blind', 'Demon', 'Enduring', 'Defiant', 'Lost', 'Dying', 'Falling', 'Soaring', 'Twisted', 'Glass',
       'Bleeding', 'Broken', 'Silent', 'Red', 'Black', 'Dark', 'Fallen', 'Patient', 'Burning', 'Final', 'Lazy',
       'Morbid', 'Crimson', 'Cursed', 'Frozen', 'Bloody', 'Banished', 'First', 'Severed', 'Empty', 'Spectral', 'Sacred',
       'Stone', 'Shattered', 'Hidden', 'Rotting', 'Devil\'s', 'Forgotten', 'Blinding', 'Fading', 'Crystal', 'Secret',
       'Cryptic', 'Smoking', 'Heaving', 'Steaming', 'Righteous', 'Purple', 'Amber', 'Wailing', 'Cosmic', 'Foolish',
       'Brooding', 'Failing', 'Gasping', 'Starving', 'Sinking', 'Holy', 'Unholy', 'Potent', 'Haunting', 'Pungent',
       'Golden', 'Iron', 'Shackled', 'Laughing', 'Damned', 'Poisoned', 'Half-eaten', 'Summoned', 'Gilded', 'Manic',
       'Precious', 'Outer', 'Little', 'Choking', 'Half-dead', 'Steely', 'Massive', 'Dismal', 'Rebel', 'Dread',
       'Sleeping', 'Magic', 'Dripping', 'Faceless', 'Shambling', 'Furious', 'Dead Man\'s', 'Perilous', 'Heavy',
       'Ancient', 'Jagged', 'Northern', 'Earthly', 'Hellish', 'Hellborn', 'Blessed', 'Buried', 'Senseless',
       'Blood-Soaked', 'Sweaty', 'Drunken', 'Scattered']
noun = ['Nightmare', 'Shark', 'Song', 'Soul', 'Harbinger', 'Rule', 'Lightning', 'Cavern', 'Chill', 'Dread', 'Ace',
        'Prophet', 'Seer', 'Armor', 'Failure', 'King', 'Rose', 'Kingdom', 'Circle', 'Autumn', 'Winter', 'Mercenary',
        'Devil', 'Hope', 'Carrier', 'Plague', 'Retribution', 'Ocean', 'Dagger', 'Spear', 'Peak', 'Trial', 'Redundancy',
        'Flicker', 'Speck', 'Meditation', 'Elegy', 'Graveyard', 'Righteousness', 'Bridge', 'Steam', 'Epidemic',
        'Infestation', 'Infection', 'Court', 'Scourge', 'Pommel', 'Sweater', 'Pestilence', 'Teardrop', 'Pandemic',
        'Corner', 'Emperor', 'Fool', 'Monk', 'Warrior', 'Hammer', 'Shelter', 'Chant', 'Guard', 'Sentiment', 'Straggler',
        'Bulwark', 'Defense', 'Corpse', 'Buffoon', 'Cadaver', 'Bastard', 'Skeleton', 'Concubine', 'Palace', 'Precipice',
        'Typhoon', 'Hurricaine', 'Quake', 'Death', 'Engine', 'Chant', 'Heart', 'Justice', 'Law', 'Thunder', 'Moon',
        'Heat', 'Fear', 'Star', 'Apollo', 'Prophet', 'Hero', 'Hydra', 'Serpent', 'Crown', 'Thorn', 'Empire', 'Summer',
        'Druid', 'God', 'Savior', 'Stallion', 'Hawk', 'Vengeance', 'Calm', 'Knife', 'Sword', 'Dream', 'Sleep', 'Stroke',
        'Flame', 'Spark', 'Fist', 'Dirge', 'Grave', 'Shroud', 'Breath', 'Smoke', 'Giant', 'Whisper', 'Night', 'Throne',
        'Pipe', 'Blade', 'Daze', 'Pyre', 'Tears', 'Mother', 'Crone', 'King', 'Father', 'Priest', 'Dawn', 'Hammer',
        'Shield', 'Hymn', 'Vanguard', 'Sentinel', 'Stranger', 'Bell', 'Mist', 'Fog', 'Jester', 'Scepter', 'Ring',
        'Skull', 'Paramour', 'Palace', 'Mountain', 'Rain', 'Gaze', 'Future', 'Gift', 'Grin', 'Omen', 'Tome', 'Wail',
        'Shriek', 'Glove', 'Gears', 'Slumber', 'Beast', 'Wolf', 'Widow', 'Witch', 'Prince', 'Skies', 'Dance', 'Spear',
        'Key', 'Fog', 'Feast', 'Cry', 'Claw', 'Peak', 'Valley', 'Shadow', 'Rhyme', 'Moan', 'Wheel', 'Doom', 'Mask',
        'Rose', 'Gods', 'Whale', 'Saga', 'Sky', 'Chalice', 'Agony', 'Misery', 'Tears', 'Rage', 'Anger', 'Laughter',
        'Terror', 'Gasp', 'Tongue', 'Cobra', 'Snake', 'Cavern', 'Corpse', 'Prophecy', 'Vagabond', 'Altar', 'Death',
        'Reckoning', 'Dragon', 'Doom', 'Shadow', 'Night', 'Witch', 'Steel', 'Fire', 'Blood', 'God', 'Demon', 'War',
        'Hammer', 'Star', 'Iron', 'Spider', 'Ice', 'Knife', 'Mountain', 'Death', 'Diamond', 'Frost', 'Moon', 'Swamp',
        'Ghost', 'Sky', 'Dawn', 'Storm', 'Tomb', 'Crypt', 'Bone', 'Hell', 'Winter', 'Wolf', 'Fall', 'Fist', 'Storm',
        'Blade', 'Star', 'Hammer', 'Witch', 'Dragon', 'Fire', 'Wheel', 'Tooth', 'Hound', 'Hand', 'Hawk', 'God',
        'Father', 'Mother', 'Knife', 'Giant', 'Steed', 'Strike', 'Slap', 'Killer', 'Mask', 'Walk', 'Fort', 'Tower',
        'Face', 'Tomb', 'Valley', 'Claw', 'King', 'Queen', 'Beast', 'Saga', 'Song', 'Chalice', 'Walker', 'Breaker',
        'Wagon', 'Shield', 'Shadow', 'Dance', 'Hole', 'Stank', 'Shriek', 'Child', 'Prince', 'Slayer', 'Briar', 'Castle']


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        owner = self.bot.get_user(GG.OWNER)
        if isinstance(error, commands.CommandNotFound):
            return
        log.debug("Error caused by message: `{}`".format(ctx.message.content))
        log.debug('\n'.join(traceback.format_exception(type(error), error, error.__traceback__)))
        if isinstance(error, CrawlerException):
            return await ctx.send(str(error))
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error,
                      (commands.MissingRequiredArgument, commands.BadArgument, commands.NoPrivateMessage, ValueError)):
            return await ctx.send("Error: " + str(
                error) + f"\nUse `{ctx.prefix}help " + ctx.command.qualified_name + "` for help.")
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send("Error: You are not allowed to run this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send("This command is on cooldown for {:.1f} seconds.".format(error.retry_after))
        elif isinstance(error, CommandInvokeError):
            original = error.original
            if isinstance(original, EvaluationError):  # PM an alias author tiny traceback
                e = original.original
                if not isinstance(e, CrawlerException):
                    tb = f"```py\nError when parsing expression {original.expression}:\n" \
                         f"{''.join(traceback.format_exception(type(e), e, e.__traceback__, limit=0, chain=False))}\n```"
                    try:
                        await ctx.author.send(tb)
                    except Exception as e:
                        log.info(f"Error sending traceback: {e}")
            if isinstance(original, CrawlerException):
                return await ctx.send(str(original))
            if isinstance(original, Forbidden):
                try:
                    return await ctx.author.send(
                        f"Error: I am missing permissions to run this command. "
                        f"Please make sure I have permission to send messages to <#{ctx.channel.id}>."
                    )
                except:
                    try:
                        return await ctx.send(f"Error: I cannot send messages to this user.")
                    except:
                        return
            if isinstance(original, NotFound):
                return await ctx.send("Error: I tried to edit or delete a message that no longer exists.")
            if isinstance(original, ValueError) and str(original) in ("No closing quotation", "No escaped character"):
                return await ctx.send("Error: No closing quotation.")
            if isinstance(original, (ClientResponseError, InvalidArgument, asyncio.TimeoutError, ClientOSError)):
                return await ctx.send("Error in Discord API. Please try again.")
            if isinstance(original, HTTPException):
                if original.response.status == 400:
                    return await ctx.send("Error: Message is too long, malformed, or empty.")
                if original.response.status == 500:
                    return await ctx.send("Error: Internal server error on Discord's end. Please try again.")
            if isinstance(original, OverflowError):
                return await ctx.send(f"Error: A number is too large for me to store.")

        error_msg = self.gen_error_message()

        await ctx.send(
            f"Error: {str(error)}\nUh oh, that wasn't supposed to happen! "
            f"Please join the Support Discord ({ctx.prefix}support) and tell the developer that: **{error_msg}!**")
        try:
            await owner.send(
                f"**{error_msg}**\n" \
                + "Error in channel {} ({}), server {} ({}): {}\nCaused by message: `{}`".format(
                    ctx.channel, ctx.channel.id, ctx.guild,
                    ctx.guild.id, repr(error),
                    ctx.message.content))
        except AttributeError:
            await owner.send(f"**{error_msg}**\n" \
                             + "Error in PM with {} ({}), shard 0: {}\nCaused by message: `{}`".format(
                ctx.author.mention, str(ctx.author), repr(error), ctx.message.content))
        for o in discord_trim(tb):
            await owner.send(o)
        log.error("Error caused by message: `{}`".format(ctx.message.content))

    def gen_error_message(self):
        subject = random.choice(adj)
        verb = random.choice(noun)
        return f"{subject} {verb}"


def setup(bot):
    log.info("[Event] Errors...")
    bot.add_cog(Errors(bot))
