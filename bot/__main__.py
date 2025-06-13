import os
from dotenv import load_dotenv
from bot import HorizonBot

load_dotenv()

import config       # load config
import db.session   # setup db session

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot = HorizonBot()