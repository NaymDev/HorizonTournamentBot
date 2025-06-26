from pathlib import Path
import discord
from discord.ext import commands

from core.services.issue_reporter import report_unhandled_exception

class HorizonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
    
    async def setup_hook(self):
        folder = Path(__file__).resolve().parent / "cogs"

        for cog_path in folder.glob("*.py"):
            await self.load_extension(f"cogs.{cog_path.stem}")