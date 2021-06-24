from crawler_utilities.handlers import logger
from utils.reminder.utils import *

log = logger.logger


class Reminder:
    def __init__(self, message, channelId, guildId, authorId, requested_date, target_date, reminded=False):
        self.message = message
        self.channelId = channelId
        self.guildId = guildId
        self.authorId = authorId
        self.requested_date = requested_date
        self.target_date = target_date
        self.reminded = reminded

    @staticmethod
    def build_reminder(
            message,
            channelId,
            guildId,
            authorId,
            requested_date,
            time_string,
            target_date=None,
            allow_default=True
    ):
        result_message = None
        time_string = time_string.strip() if time_string is not None else None
        if target_date is None:
            if time_string is not None:
                requested_date = pytz.UTC.localize(requested_date)
                target_date = parse_time(time_string, requested_date)
                log.debug(f"Target date: {get_datetime_string(target_date)}")

                if target_date is None:
                    if allow_default:
                        result_message = f"Could not parse date: \"{time_string}\", defaulting to one day"
                        log.info(result_message)
                        target_date = parse_time("1 day", requested_date)
                    else:
                        result_message = f"Could not parse date: \"{time_string}\", defaulting not allowed"
                        log.info(result_message)
                        return None, result_message
                elif target_date < requested_date:
                    result_message = f"This time, {time_string}, was interpreted as " \
                                     f"{get_datetime_string(target_date)}, which is in the past"
                    log.info(result_message)
                    return None, result_message

            else:
                if allow_default:
                    result_message = "Could not find a time in message, defaulting to one day"
                    log.info(result_message)
                    target_date = parse_time("1 day", requested_date)
                else:
                    result_message = f"Could not find a time in message, defaulting not allowed"
                    log.info(result_message)
                    return None, result_message

        reminder = Reminder(
            message=message,
            channelId=channelId,
            guildId=guildId,
            authorId=authorId,
            requested_date=requested_date,
            target_date=target_date
        )

        return reminder, result_message

    @classmethod
    def from_dict(cls, reminder_dict):
        return cls(**reminder_dict)

    def to_dict(self):
        return {"message": self.message, "channelId": self.channelId, "guildId": self.guildId, "authorId": self.authorId,
                "requested_date": self.requested_date, "target_date": self.target_date, "reminded": self.reminded}

    async def render_message_confirmation(self, bot, result_message):
        bldr = str_bldr()

        if result_message is not None:
            bldr.append(result_message)
            bldr.append("\n\n")
        else:
            if self.target_date < datetime_now():
                bldr.append("I will be messaging you on ")
            else:
                bldr.append("I will be messaging you in ")
                bldr.append(render_time_diff(datetime_now(), self.target_date))
                bldr.append(" on ")
            bldr.append(render_time(self.target_date))
            url = await getJumpUrl(self, bot)
            if url is None:
                bldr.append("\n\nTo remind you")
            elif url == "deleted":
                bldr.append("\n\nTo remind you about a message, but it's seemingly deleted.")
            else:
                bldr.append("\n\nTo remind you about [this message](")
                bldr.append(url)
                bldr.append(").")

        return bldr

    async def render_notification(self, bot):
        bldr = str_bldr()
        url = await getJumpUrl(self, bot)
        if url is None:
            bldr.append("I'm here to remind you.")
        elif url == "deleted":
            bldr.append("\n\nI'm here to remind you about a message, but it's seemingly deleted.")
        else:
            bldr.append("I'm here to remind you of [this message](")
            bldr.append(url)
            bldr.append(").")
        bldr.append("\n\n")
        bldr.append("You requested this reminder on: ")
        bldr.append(render_time(self.requested_date))
        bldr.append("\n\n")
        return bldr
