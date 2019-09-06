import logging
import random
import re

log = logging.getLogger(__name__)


class SearchException(Exception):
    pass


def discord_trim(string):
    result = []
    trimLen = 0
    lastLen = 0
    while trimLen <= len(string):
        trimLen += 1999
        result.append(string[lastLen:trimLen])
        lastLen += 1999
    return result


def gen_error_message():
    subject = random.choice(['A kobold', 'The green dragon', 'The Frost Mage', 'DiscordCrawler', 'The wizard',
                             'An iron golem', 'Your mom', 'This bot', 'You', 'Me', 'The president',
                             'The Queen', 'Xanathar', 'Volo', 'This world'])
    verb = random.choice(['must be', 'should be', 'has been', 'will be', 'is being', 'was being'])
    thing_to_do = random.choice(['stopped', 'killed', 'talked to', 'found', 'destroyed', 'fought'])
    return f"{subject} {verb} {thing_to_do}"


def a_or_an(string, upper=False):
    if string.startswith('^') or string.endswith('^'):
        return string.strip('^')
    if re.match('[AEIOUaeiou].*', string):
        return 'an {0}'.format(string) if not upper else f'An {string}'
    return 'a {0}'.format(string) if not upper else f'A {string}'


def camel_to_title(string):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', string).title()