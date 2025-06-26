from pathlib import Path
import discord
from discord.ext import commands

class HorizonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        
        
        print("------")
        for guild in self.guilds:
            for cmd in await self.tree.sync():
                print(
                    f"Synced command {cmd.name} for guild {guild.name} ({guild.id})"
                )
            print(f"Synced commands for guild {guild.name} ({guild.id})")
        print("------")
        
    
    async def setup_hook(self):
        folder = Path(__file__).resolve().parent / "cogs"

        for cog_path in folder.glob("*.py"):
            await self.load_extension(f"cogs.{cog_path.stem}")