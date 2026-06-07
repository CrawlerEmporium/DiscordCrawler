import io

import discord
import imagehash
from PIL import Image, ImageOps, ImageFile

from utils import globals as GG

ImageFile.LOAD_TRUNCATED_IMAGES = True

def imagehash_to_int(hash_value) -> int:
    """Convert an imagehash.ImageHash value to a stable integer."""
    return int(str(hash_value), 16)


def db_hash_value(hash_value: int) -> str:
    """Convert a hash integer to a Mongo-safe string value."""
    return str(hash_value)


def normalize_spam_doc(doc: dict) -> tuple[int, dict]:
    """Normalize a spam image document for in-memory cache use."""
    hash_value = int(doc["image_hash"])
    normalized = dict(doc)
    normalized["image_hash"] = db_hash_value(hash_value)
    if "dhash" in normalized:
        normalized["dhash"] = db_hash_value(int(normalized["dhash"]))
    if "ahash" in normalized:
        normalized["ahash"] = db_hash_value(int(normalized["ahash"]))
    return hash_value, normalized


def hash_image(image_bytes: bytes) -> dict:
    """Return perceptual hashes for raw image bytes."""
    with Image.open(io.BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        image.load()
        image = image.convert("RGB")
        return {
            "phash": imagehash_to_int(imagehash.phash(image)),
            "dhash": imagehash_to_int(imagehash.dhash(image)),
            "ahash": imagehash_to_int(imagehash.average_hash(image)),
        }


def is_match(computed: dict, known: dict) -> bool:
    """Check if any hash type is within threshold."""
    threshold = 7
    for hash_type in ["phash", "dhash", "ahash"]:
        if hash_type in computed and hash_type in known:
            dist = bin(
                computed[hash_type] ^ known[hash_type]
            ).count("1")
            if dist <= threshold:
                return True
    return False


def is_image(attachment: discord.Attachment) -> bool:
    """Check if an attachment is an image based on URL extension."""
    return any(
        attachment.filename.lower().endswith(ext)
        for ext in GG.IMAGE_EXTENSIONS
    )
