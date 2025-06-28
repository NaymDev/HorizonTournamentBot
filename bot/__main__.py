import os
from dotenv import load_dotenv
from bot import HorizonBot
import asyncio
from db import session

load_dotenv()

import config       # load config  # noqa: E402, F401

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise EnvironmentError("Environment variable DISCORD_TOKEN is not set or empty")

async def setup():
    await session.init_db()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(setup())
    bot = HorizonBot()
    bot.run(DISCORD_TOKEN)