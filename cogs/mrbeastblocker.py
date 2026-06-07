from typing import Union

import requests
from datetime import datetime

import discord
from discord import SlashCommandGroup, option
from discord.ext import commands, tasks

from utils import globals as GG
from utils.imagehashing import db_hash_value, normalize_spam_doc, hash_image, is_match, is_image

log = GG.log


class MrBeastBlocker(commands.Cog):
    """Detects spam/scam images using perceptual hashing."""

    def __init__(self, bot):
        self.bot = bot
        self.spam_hashes = {}
        self.hash_cache_reload.start()

    spam = SlashCommandGroup("spam", "Commands to manage spam detection")

    @tasks.loop(hours=1)
    async def hash_cache_reload(self):
        """Reload known spam hashes from the database every hour."""
        docs = await GG.MDB["spam_images"].find({}).to_list(length=None)
        self.spam_hashes.clear()
        for doc in docs:
            h, normalized = normalize_spam_doc(doc)
            self.spam_hashes[h] = normalized
        log.info(f"Spam hash cache reloaded with {len(self.spam_hashes)} entries")

    @hash_cache_reload.before_loop
    async def before_hash_cache_reload(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Check message attachments against known spam image hashes."""
        if message.author.bot:
            return
        if not message.attachments:
            return

        for attachment in message.attachments:
            if not is_image(attachment):
                continue
            # Skip large files to avoid memory issues
            if attachment.size and attachment.size > 10 * 1024 * 1024:
                continue

            try:
                image_bytes = await attachment.read()
                hashes = hash_image(image_bytes)
            except Exception:
                continue

            # Check against in-memory cache
            for hash_type, hash_val in hashes.items():
                if hash_val in self.spam_hashes:
                    known = self.spam_hashes[hash_val]
                    known_hashes = {
                        "phash": int(known["image_hash"]),
                        "dhash": int(known.get("dhash", 0)),
                        "ahash": int(known.get("ahash", 0)),
                    }
                    if is_match(hashes, known_hashes):
                        await self._handle_spam(message, known, hash_type, known_hashes)
                        return

    async def _handle_spam(self, message, known, hash_type, known_hashes):
        """Delete spam message and notify mod log channel."""
        match_url = (
            f"https://discord.com/channels/"
            f"{message.guild.id}/{message.channel.id}/{message.id}"
        )

        # Get per-guild mod log channel
        settings = await GG.MDB["bot_settings"].find_one(
            {"guild_id": message.guild.id}
        )

        mod_channel_id = (
            settings.get("mod_log_channel_id")
            if settings
            else None
        )

        # Record match
        await GG.MDB["spam_matches"].insert_one({
            "hash_type": hash_type,
            "posting_user": message.author.id,
            "message_url": match_url,
            "channel_id": message.channel.id,
            "guild_id": message.guild.id,
            "matched_at": datetime.utcnow(),
            "action_taken": "deleted",
            "matched_against": known.get("original_url", "unknown"),
        })

        # Log the event
        log.warning(
            f"Spam detected: {message.author} ({message.author.id}) in "
            f"#{message.channel} ({message.channel.id}), "
            f"hash={hash_type}, url={match_url}"
        )

        # Send alert to mod log channel
        if mod_channel_id:
            mod_channel = self.bot.get_channel(mod_channel_id)
            if mod_channel:
                embed = discord.Embed(
                    title="Spam Image Detected",
                    colour=0xff4444,
                    description=(
                        f"Image posted by {message.author.mention} (**{message.author}**) matches a known "
                        f"spam image.\n"
                        f"Matching hash type: `{hash_type}`\n"
                        f"Source: {known.get('original_url', 'unknown')}"
                    ),
                )

                if hash_type == "phash":
                    phash_msg = f"**{known_hashes['phash']}**" if known_hashes.get('phash') else ""
                else:
                    phash_msg = f"{known_hashes['phash']}" if known_hashes.get('phash') else ""

                if hash_type == "dhash":
                    dhash_msg = f"**{known_hashes['dhash']}**" if known_hashes.get('dhash') else ""
                else:
                    dhash_msg = f"{known_hashes['dhash']}" if known_hashes.get('dhash') else ""

                if hash_type == "ahash":
                    ahash_msg = f"**{known_hashes['ahash']}**" if known_hashes.get('ahash') else ""
                else:
                    ahash_msg = f"{known_hashes['ahash']}" if known_hashes.get('ahash') else ""

                embed.add_field(name="phash", value=phash_msg, inline=True)
                embed.add_field(name="dhash", value=dhash_msg, inline=True)
                embed.add_field(name="ahash", value=ahash_msg, inline=True)

                await mod_channel.send(embed=embed)

        # Delete the message
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    @spam.command(name="add")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def addspam(self, ctx, url: str = None):
        """Add a known spam image to the database."""
        await ctx.defer()

        image_bytes = None
        # Try getting image from replied message
        if url is None and ctx.message.reference:
            try:
                ref = await ctx.message.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if ref.attachments:
                    image_bytes = await ref.attachments[0].read()
            except Exception:
                pass

        # Try downloading from URL
        if image_bytes is None and url is not None:
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "image" in content_type:
                        image_bytes = resp.content
            except Exception:
                pass

        if image_bytes is None:
            await ctx.respond(
                embed=discord.Embed(
                    title="Error",
                    description="Please provide a URL or reply to an image.",
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        hashes = hash_image(image_bytes)

        # Check for duplicates
        existing = await GG.MDB["spam_images"].find_one(
            {"image_hash": db_hash_value(hashes["phash"])}
        )
        if existing:
            await ctx.respond(
                embed=discord.Embed(
                    title="Already Exists",
                    description=(
                        "This image (or a very similar one) is already in "
                        "the database."
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        await GG.MDB["spam_images"].insert_one({
            "image_hash": db_hash_value(hashes["phash"]),
            "dhash": db_hash_value(hashes["dhash"]),
            "ahash": db_hash_value(hashes["ahash"]),
            "original_url": url or f"added_by_{ctx.author.id}",
            "added_by": ctx.author.id,
            "added_at": datetime.utcnow(),
            "source": "manual",
            "guild_id": ctx.guild.id if ctx.guild else None,
            "channel_id": ctx.channel.id,
        })

        # Reload cache
        await self.hash_cache_reload()

        await ctx.respond(
            embed=discord.Embed(
                title="Spam Image Added",
                description=(
                    f"Image added successfully.\n"
                    f"PHASH: `{hashes['phash']}`"
                ),
                colour=0x44aa44,
            ),
        )
        log.info(f"Admin added spam image from {url} by {ctx.author}")

    @spam.command(name="list")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def listspam(self, ctx, page: int = 1):
        """Paginated list of known spam images."""
        await ctx.defer()

        count = await GG.MDB["spam_images"].count_documents({})
        if count == 0:
            await ctx.respond(
                embed=discord.Embed(
                    title="No Spam Images",
                    description=(
                        "The database contains no known spam images yet."
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        per_page = 10
        offset = (page - 1) * per_page
        total_pages = (count // per_page) + (1 if count % per_page else 0)

        docs = await (
            GG.MDB["spam_images"]
            .find({})
            .sort("added_at", -1)
            .skip(offset)
            .limit(per_page)
            .to_list(length=per_page)
        )

        embed = discord.Embed(
            title=f"Known Spam Images (Page {page}/{total_pages})",
            description=f"Total entries: {count}",
            colour=0x55aa55,
        )

        for doc in docs:
            source = doc.get("source", "unknown")
            added_by = doc.get("added_by", "unknown")
            url = doc.get("original_url", "N/A")
            value = (
                f"Source: `{source}` | Added by: `{added_by}`\n"
                f"URL: {url}"
            )
            embed.add_field(
                name=f"Hash: `{doc['image_hash']}`",
                value=value,
                inline=False,
            )

        embed.set_footer(text=f"Page {page} of {total_pages}")
        await ctx.respond(embed=embed)

    @spam.command(name="remove")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def removespam(self, ctx, phash: str):
        """Remove a spam image by its phash value."""
        await ctx.defer()

        try:
            hash_val = int(phash)
        except ValueError:
            await ctx.respond(
                embed=discord.Embed(
                    title="Invalid Hash",
                    description=f"`{phash}` is not a valid hash value.",
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        result = await GG.MDB["spam_images"].delete_one(
            {"image_hash": db_hash_value(hash_val)}
        )
        if result.deleted_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    title="Removed",
                    description=(
                        f"Spam image with hash `{phash}` has been removed."
                    ),
                    colour=0x44aa44,
                ),
            )
            log.info(f"Admin removed spam image {phash}")
            await self.hash_cache_reload()
        else:
            await ctx.respond(
                embed=discord.Embed(
                    title="Not Found",
                    description=f"No spam image found with hash `{phash}`.",
                    colour=0xff0000,
                ),
                ephemeral=True,
            )

    @spam.command(name="modlog")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @option("subcommand", choices=["set", "unset", "show"])
    @option("channel", Union[discord.TextChannel], description="Select a Channel", required=False)
    async def modlog(self, ctx, subcommand: str = None, channel: discord.TextChannel = None):
        """
        Manage the mod log channel for spam alerts.
        Usage:
          /modlog set <channel>  - Set this channel as the mod log channel
          /modlog unset          - Clear the mod log channel
          /modlog show           - Show current mod log channel
        """
        await ctx.defer()

        settings = await GG.MDB["bot_settings"].find_one(
            {"guild_id": ctx.guild.id}
        )
        if settings is None:
            settings = {"guild_id": ctx.guild.id}
            await GG.MDB["bot_settings"].insert_one(settings)

        if subcommand == "set":
            if channel is None:
                await ctx.respond(
                    embed=discord.Embed(
                        title="Error",
                        description=(
                            "Please specify a channel. "
                            "Usage: `/modlog set <channel>`"
                        ),
                        colour=0xff0000,
                    ),
                    ephemeral=True,
                )
                return
            settings["mod_log_channel_id"] = channel.id
            await GG.MDB["bot_settings"].replace_one(
                {"guild_id": ctx.guild.id}, settings
            )
            await ctx.respond(
                embed=discord.Embed(
                    title="Mod Log Channel Set",
                    description=(
                        f"Spam detection alerts will be sent to **{channel}**."
                    ),
                    colour=0x44aa44,
                ),
            )
            log.info(f"Admin set mod log to {channel} in {ctx.guild}")

        elif subcommand == "unset":
            if not settings.get("mod_log_channel_id"):
                await ctx.respond(
                    embed=discord.Embed(
                        title="Not Set",
                        description=(
                            "No mod log channel is configured for this guild."
                        ),
                        colour=0xff0000,
                    ),
                    ephemeral=True,
                )
                return
            settings["mod_log_channel_id"] = None
            await GG.MDB["bot_settings"].replace_one(
                {"guild_id": ctx.guild.id}, settings
            )
            await ctx.respond(
                embed=discord.Embed(
                    title="Mod Log Cleared",
                    description=(
                        "Spam detection alerts will no longer be sent to a "
                        "log channel."
                    ),
                    colour=0x44aa44,
                ),
            )
            log.info(f"Admin cleared mod log in {ctx.guild}")

        elif subcommand == "show":
            current = settings.get("mod_log_channel_id")
            if current:
                mod_channel = ctx.guild.get_channel(current)
                display = (
                    mod_channel.mention
                    if mod_channel
                    else f"<#{current}>"
                )
            else:
                display = "Not set"
            await ctx.respond(
                embed=discord.Embed(
                    title="Mod Log Channel",
                    description=f"Current mod log channel: {display}",
                    colour=0x55aa55,
                ),
            )

        else:
            await ctx.respond(
                embed=discord.Embed(
                    title="Invalid Subcommand",
                    description=(
                        "Usage: `/modlog set <channel>`, "
                        "`/modlog unset`, or `/modlog show`"
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )

    @spam.command(name="showsetup")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def modsetup(self, ctx):
        """Show current moderation setup."""
        await ctx.defer()

        settings = await GG.MDB["bot_settings"].find_one(
            {"guild_id": ctx.guild.id}
        )
        if settings is None:
            settings = {"guild_id": ctx.guild.id}

        mod_channel_id = settings.get("mod_log_channel_id")
        mod_channel = (
            ctx.guild.get_channel(mod_channel_id)
            if mod_channel_id
            else None
        )
        channel_display = (
            mod_channel.mention if mod_channel else "Not set"
        )

        await ctx.respond(
            embed=discord.Embed(
                title=f"Moderation Settings ({ctx.guild})",
                description=(
                    f"**Mod Log Channel:** {channel_display}\n"
                    f"**Delete Matching:** Yes\n"
                    f"**Notify Mods:** Yes"
                ),
                colour=0x55aa55,
            ),
        )

    @spam.command(name="train")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def train(self, ctx, url: str):
        """
        Train the spam detector by adding all images from a message URL.
        Usage: `/train <discord message url>`
        """
        await ctx.defer()

        # Parse message URL: https://discord.com/channels/{guild}/{channel}/{message}
        import re
        match = re.match(
            r'https://(?:discord\.com|discordapp\.com)/channels/'
            r'(?:(\d+)|@everyone)/(\d+)/(\d+)',
            url.strip(),
        )
        if not match:
            await ctx.respond(
                embed=discord.Embed(
                    title="Invalid URL",
                    description=(
                        "Please provide a valid Discord message URL. "
                        "Example: `https://discord.com/channels/123456789/987654321/1122334455`"
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        guild_id = int(match.group(1))
        channel_id = int(match.group(2))
        message_id = int(match.group(3))

        # Fetch the target guild (bot may not be in it)
        try:
            target_guild = self.bot.get_guild(guild_id)
            if target_guild is None:
                target_guild = await self.bot.fetch_guild(guild_id)
        except Exception:
            await ctx.respond(
                embed=discord.Embed(
                    title="Guild Not Found",
                    description=(
                        f"Could not access guild `{guild_id}`. "
                        f"Make sure the bot is in that server."
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        # Fetch the channel
        try:
            channel = target_guild.get_channel(channel_id)
            if channel is None:
                channel = await self.bot.fetch_channel(channel_id)
        except Exception:
            await ctx.respond(
                embed=discord.Embed(
                    title="Channel Not Found",
                    description=f"Could not access channel `{channel_id}` in guild `{guild_id}`.",
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        # Fetch the message
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.respond(
                embed=discord.Embed(
                    title="Message Not Found",
                    description=f"Could not find message `{message_id}`.",
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        return await self.handle_message(ctx, message)

    @commands.message_command(name="Staff: Train Spam detector")
    @commands.guild_only()
    async def train_message(self, ctx, message: discord.Message):
        await ctx.defer(ephemeral=True)
        if not GG.is_staff_bool(ctx):
            return await ctx.respond("You do not have the required permissions to use this command.", ephemeral=True)

        return await self.handle_message(ctx, message, True)

    async def handle_message(self, ctx, message: discord.Message, ephemeral=False):
        """Handle a message for spam detection."""
        if not message.attachments:
            await ctx.respond(
                embed=discord.Embed(
                    title="No Attachments",
                    description="That message does not contain any attachments.",
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        # Collect image attachments
        image_attachments = [
            a for a in message.attachments
            if is_image(a)
        ]

        if not image_attachments:
            await ctx.respond(
                embed=discord.Embed(
                    title="No Images",
                    description=(
                        "That message has attachments but none are images "
                        f"({', '.join(GG.IMAGE_EXTENSIONS)})."
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        # Process each image
        added = 0
        skipped = 0
        failed = []

        url = message.jump_url
        guild_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.id

        for attachment in image_attachments:
            try:
                image_bytes = await attachment.read()

                hashes = hash_image(image_bytes)

                # Skip duplicates
                existing = await GG.MDB["spam_images"].find_one(
                    {"image_hash": db_hash_value(hashes["phash"])}
                )
                if existing:
                    skipped += 1
                    continue

                await GG.MDB["spam_images"].insert_one({
                    "image_hash": db_hash_value(hashes["phash"]),
                    "dhash": db_hash_value(hashes["dhash"]),
                    "ahash": db_hash_value(hashes["ahash"]),
                    "original_url": url.strip(),
                    "added_by": ctx.author.id,
                    "added_at": datetime.utcnow(),
                    "source": "train",
                    "message_url": url.strip(),
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                })
                added += 1
            except Exception as exc:
                log.exception(
                    f"Failed to process attachment {attachment.filename} "
                    f"from message {message_id} in channel {channel_id}",
                )
                failed.append(attachment.filename)
                continue

        # Reload cache
        await self.hash_cache_reload()

        # Build result message
        parts = [f"Added **{added}** new spam image(s)."]
        if skipped:
            parts.append(f"Skipped **{skipped}** duplicate(s).")
        if failed:
            failed_names = ", ".join(failed)
            parts.append(
                f"Failed to process **{len(failed)}** image(s): {failed_names}."
            )
        detail = ", ".join(parts)

        await ctx.respond(
            embed=discord.Embed(
                title="Training Complete",
                description=detail,
                colour=0x44aa44,
            ),
            ephemeral=ephemeral
        )
        log.info(
            f"Admin trained spam detector with message {url}: "
            f"+{added}, skipped={skipped}, failed={len(failed)}"
        )

    @spam.command(name="settings")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @option("setting", description="Setting to toggle", choices=["delete_matching","notify_mods", "notify_author"])
    @option("value", description="True/False", choices=["True", "False"])
    async def togglesetting(self, ctx, setting: str, value: str = "true"):
        """
        Toggle a moderation setting.
        Settings: delete_matching, notify_mods, notify_author
        """
        await ctx.defer()

        valid_settings = {
            "delete_matching",
            "notify_mods",
            "notify_author",
        }
        if setting not in valid_settings:
            await ctx.respond(
                embed=discord.Embed(
                    title="Invalid Setting",
                    description=(
                        f"Valid settings: "
                        f"{', '.join(sorted(valid_settings))}"
                    ),
                    colour=0xff0000,
                ),
                ephemeral=True,
            )
            return

        bool_val = value.lower() in (
            "true", "yes", "1", "on", "enable"
        )
        settings = await GG.MDB["bot_settings"].find_one(
            {"guild_id": ctx.guild.id}
        )
        if settings is None:
            settings = {"guild_id": ctx.guild.id}
        settings[setting] = bool_val
        await GG.MDB["bot_settings"].replace_one(
            {"guild_id": ctx.guild.id}, settings
        )

        await ctx.respond(
            embed=discord.Embed(
                title="Setting Updated",
                description=(
                    f"**{setting}** has been set to `{value}` "
                    f"in **{ctx.guild}**."
                ),
                colour=0x44aa44,
            ),
        )
        log.info(f"Admin toggled {setting}={value} in {ctx.guild}")


def setup(bot):
    log.info("[Cog] MrBeastBlocker")
    bot.add_cog(MrBeastBlocker(bot))