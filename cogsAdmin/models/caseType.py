from enum import IntEnum


class CaseType(IntEnum):
    NOTE = 0  # Blue
    WARNING = 1  # Yellow
    MUTE = 2  # Dark Grey
    TEMPBAN = 3  # Deep Orange
    BAN = 4  # Red
