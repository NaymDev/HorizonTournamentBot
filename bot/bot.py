import discord
from discord.ext import commands

class HorizonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Needed for message content access
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")