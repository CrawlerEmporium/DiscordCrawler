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

async def main():
    asyncio.ensure_future(DBService.while_commit())


if __name__ == 'DBService':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
