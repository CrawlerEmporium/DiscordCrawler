import asyncio

import motor.motor_asyncio
from cryptography.fernet import Fernet
from environs import Env

env = Env()
env.read_env()

MONGODB = env('MONGODB')
MDB = motor.motor_asyncio.AsyncIOMotorClient(MONGODB)['discordCrawler']
KEY = env('KEY')


async def run():
    entries = await MDB['reports'].find({}).to_list(length=None)
    for entry in entries:
        print(entry['user'])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
