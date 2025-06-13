import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db.session import SessionLocal

load_dotenv()

class HorizonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Needed for message content access
        super().__init__(command_prefix="!", intents=intents)
        
        # You can add cogs here if you want
        self.add_cog(Greetings(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

# Example cog in the same file (better separate but small example here)
class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello")
    async def hello(self, ctx):
        session = SessionLocal()
        user = User(name=str(ctx.author))
        session.add(user)
        session.commit()
        session.close()

        await ctx.send(f"Hello {ctx.author.name}!")

