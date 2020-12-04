from enum import IntEnum


class CaseType(IntEnum):
    NOTE = 0  # Blue
    WARNING = 1  # Yellow
    KICK = 2  # Orange
    TEMPBAN = 3  # Deep Orange
    BAN = 4  # Red
