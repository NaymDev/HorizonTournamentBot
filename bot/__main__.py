import os
from dotenv import find_dotenv, load_dotenv
from bot import HorizonBot
import asyncio
from db import session

load_dotenv(dotenv_path=".env", override=True)

import config       # load config  # noqa: E402, F401

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise EnvironmentError("Environment variable DISCORD_TOKEN is not set or empty")

async def setup():
    await session.init_db()

if __name__ == "__main__":
    asyncio.run(setup())
    bot = HorizonBot()
    bot.run(DISCORD_TOKEN)