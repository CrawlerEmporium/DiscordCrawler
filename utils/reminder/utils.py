import re
import dateparser
import pytz
import parsedatetime

from datetime import datetime, timedelta
from dateparser.search import search_dates
from dateutil.relativedelta import relativedelta

debug_time = None
cal = parsedatetime.Calendar()


def find_reminder_message(body, trigger):
    line_match = re.search(r'(?:{trigger}.+)(?:(?:\[)([^\]]+?)(?:\])|(?:\")([^\"]+?)(?:\")|(?:“)([^”]*?)(?:”))(?:[^(]|\n|$)'.format(trigger=trigger), body, flags=re.IGNORECASE)
    if line_match:
        return line_match.group(1) or line_match.group(2) or line_match.group(3)

    match = re.search(r'(?:(?:\[)([^\]]+?)(?:\])|(?:\")([^\"]+?)(?:\")|(?:“)([^”]*?)(?:”))(?:[^(]|\n|$)', body, flags=re.IGNORECASE)
    if match:
        return match.group(1) or match.group(2) or match.group(3)
    else:
        return None


def find_reminder_time(body):
    times = re.findall(r'(.*?)(?:\[|\n|\"|“|$)', body, flags=re.IGNORECASE)
    if len(times) > 0 and times[0] != "":
        return times[0][:80]
    else:
        return None


def parse_time(time_string, base_time):
    base_time = datetime_as_timezone(base_time, None)

    try:
        date_time = dateparser.parse(
            time_string,
            languages=['en'],
            settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
    except Exception:
        date_time = None

    if date_time is None:
        try:
            results = search_dates(
                time_string,
                languages=['en'],
                settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
            if results is not None:
                temp_time = results[0][1]
                if temp_time.tzinfo is None:
                    temp_time = datetime_force_utc(temp_time)

                if temp_time > base_time:
                    date_time = results[0][1]
            else:
                date_time = None
        except Exception:
            date_time = None

    if date_time is None:
        try:
            date_time, result_code = cal.parseDT(time_string, base_time)
            if result_code == 0:
                date_time = None
        except Exception:
            date_time = None

    if date_time is None:
        return None

    if date_time.tzinfo is None:
        date_time = datetime_force_utc(date_time)

    date_time = datetime_as_utc(date_time)

    return date_time


def render_time(date_time, user=None, format_string=None):
    timezone = user.timezone if user is not None else None
    time_format = user.time_format if user is not None else None
    if format_string is None:
        if time_format == "12":
            format_string = "%Y-%m-%d %I:%M:%S %p %Z"
        else:
            format_string = "%Y-%m-%d %H:%M:%S %Z"

    bldr = str_bldr()
    bldr.append("[**")
    bldr.append(datetime_as_timezone(date_time, timezone).strftime(format_string))
    bldr.append("**](http://www.wolframalpha.com/input/?i=")
    bldr.append(date_time.strftime('%Y-%m-%d %H:%M:%S %Z').replace(" ", "%20"))
    bldr.append(" To Local Time".replace(" ", "%20"))
    bldr.append(")")
    return ''.join(bldr)


def render_time_diff(start_date, end_date):
    seconds = int((end_date - start_date).total_seconds())
    if seconds > 59:
        try:
            adjusted_end_date = start_date + relativedelta(seconds=int(min(seconds * 1.02, seconds + 60 * 60 * 24)))
        except OverflowError:
            adjusted_end_date = datetime_force_utc(datetime(year=9999, month=12, day=31))

        delta = relativedelta(adjusted_end_date, start_date)
    else:
        delta = relativedelta(end_date, start_date)
    if delta.years > 0:
        return f"{delta.years} year{('s' if delta.years > 1 else '')}"
    elif delta.months > 0:
        return f"{delta.months} month{('s' if delta.months > 1 else '')}"
    elif delta.days > 0:
        return f"{delta.days} day{('s' if delta.days > 1 else '')}"
    elif delta.hours > 0:
        return f"{delta.hours} hour{('s' if delta.hours > 1 else '')}"
    elif delta.minutes > 0:
        return f"{delta.minutes} minute{('s' if delta.minutes > 1 else '')}"
    elif delta.seconds > 0:
        return f"{delta.seconds} second{('s' if delta.seconds > 1 else '')}"
    else:
        return ""


def datetime_as_timezone(date_time, timezone_string):
    if timezone_string is None:
        return date_time
    else:
        return date_time.astimezone(pytz.timezone(timezone_string))


def datetime_as_utc(date_time):
    return date_time.astimezone(pytz.utc)


def datetime_force_utc(date_time):
    return pytz.utc.localize(date_time)


def time_offset(date_time, hours=0, minutes=0, seconds=0):
    if date_time is None:
        return True
    return date_time < datetime_now() - timedelta(hours=hours, minutes=minutes, seconds=seconds)


def add_years(date_time, years):
    try:
        return date_time.replace(year=date_time.year + years)
    except ValueError:
        return date_time + (datetime(date_time.year + years, 3, 1) - datetime(date_time.year, 3, 1))


def datetime_now():
    if debug_time is None:
        return datetime_force_utc(datetime.utcnow().replace(microsecond=0))
    else:
        return debug_time


def datetime_from_timestamp(timestamp):
    return datetime_force_utc(datetime.utcfromtimestamp(timestamp))


def get_datetime_string(date_time, convert_utc=True, format_string="%Y-%m-%d %H:%M:%S"):
    if date_time is None:
        return ""
    if convert_utc:
        date_time = datetime_as_utc(date_time)
    return date_time.strftime(format_string)


def parse_datetime_string(date_time_string, force_utc=True, format_string="%Y-%m-%d %H:%M:%S"):
    if date_time_string is None or date_time_string == "None" or date_time_string == "":
        return None
    date_time = datetime.strptime(date_time_string, format_string)
    if force_utc:
        date_time = datetime_force_utc(date_time)
    return date_time


def str_bldr():
    return []


async def getJumpUrl(reminder, bot):
    if reminder.message is None:
        return None
    try:
        channel = await bot.fetch_channel(reminder.channelId)
        message = await channel.fetch_message(reminder.message)
    except:
        return "deleted"
    return message.jump_url
