from pathlib import Path
import discord
from discord.ext import commands

class HorizonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        
        print("------")
        await self.tree.sync()
        print("------")
    
    async def setup_hook(self):
        folder = Path(__file__).resolve().parent / "cogs"

        for cog_path in folder.glob("*.py"):
            await self.load_extension(f"cogs.{cog_path.stem}")

#       TODO:                                                                           #
#       - fetch/use brackets from challonge                                             #
#       - add ban method in service layer which will check teams, signups, etc.         #
#       - ban command using the according service layer                                 #