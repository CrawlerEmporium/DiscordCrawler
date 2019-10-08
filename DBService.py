import sqlite3
import asyncio
import time

from utils import logger

log = logger.logger

conn = sqlite3.connect('DiscordCrawler.db')
c = conn.cursor()

c.execute(
    "CREATE TABLE IF NOT EXISTS Prefixes (Guild INTEGER unique, Prefix TEXT)")
c.execute(
    "CREATE TABLE IF NOT EXISTS Terms (Guild INTEGER, Term TEXT, PRIMARY KEY (Guild, Term))")
c.execute(
    "CREATE TABLE IF NOT EXISTS Grey (Guild INTEGER, Term TEXT, PRIMARY KEY (Guild, Term))")
c.execute(
    "CREATE TABLE IF NOT EXISTS PersonalQuotes (User INTEGER, Trigger TEXT, Response TEXT, Attachments TEXT, PRIMARY KEY (User, Trigger))")
c.execute(
    "CREATE TABLE IF NOT EXISTS GlobalCommands (Guild INTEGER, Trigger TEXT, Response TEXT, Attachments TEXT, PRIMARY KEY (Guild, Trigger))")
c.execute(
    "CREATE TABLE IF NOT EXISTS Reports (User INTEGER, Message INTEGER, PRIMARY KEY (User, Message))")
c.execute(
    "CREATE TABLE IF NOT EXISTS ChannelInfo (Guild INTEGER, Channel INTEGER, Type TEXT, PRIMARY KEY (Guild, Channel))")
c.execute(
    "CREATE TABLE IF NOT EXISTS ServerStaff (Guild INTEGER, Roles INTEGER, PRIMARY KEY(Guild, Roles))")
c.execute(
    "CREATE TABLE IF NOT EXISTS Commands (Command Text unique, Count Integer, LastUsed Timestamp default (strftime('%s', 'now')))")
c.execute(
    "CREATE TABLE IF NOT EXISTS ReactionRoles (GuildId INTEGER, MessageId INTEGER, RoleId INTEGER, Emoji TEXT, PRIMARY KEY (MessageId, RoleId, Emoji))")


# noinspection PyMethodParameters
class DBService:

    def exec(sql):
        try:
            return c.execute(sql)
        except sqlite3.IntegrityError:
            raise Exception

    def commit():
        log.info("Commiting changes to the Database.")
        return conn.commit()

    async def while_commit():
        while True:
            await asyncio.sleep(60)
            conn.commit()

    async def save_reporter(message, reporter):
        DBService.exec("INSERT INTO Reports (User, Message) VALUES (" + str(reporter) + ", " + str(message) + ")")

async def main():
    asyncio.ensure_future(DBService.while_commit())


if __name__ == 'DBService':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
