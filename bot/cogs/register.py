import random
import discord
from discord.ext import commands

from db.session import SessionLocal
from config import CONFIG
from core.repositories.players import PlayerRepository
from core.services.minecraft_account import MinecraftAccountService, PlayerNotFound
from core.repositories.minecraft import MinecraftRepository

class RegisterCog(commands.Cog):
    def __init__(self, bot: commands.Bot, session_factory):
        self.bot = bot
        self.session_factory = session_factory

    @discord.app_commands.command()
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            player_repo = PlayerRepository(session)
            
            if (await player_repo.get_by_discord_id(str(interaction.user.id))):
                await interaction.followup.send("👋 Hey there. Welcome back to horizon", ephemeral=True)
                return
            
            await player_repo.create_player(
                interaction.user.id,
                interaction.user.name
            )
            
            await interaction.followup.send(
                "👋 Hey there. Welcome to horizon",
                ephemeral=True
            )
            
            await interaction.channel.send(random.choice(CONFIG.register.hello_messages).replace("{user}", interaction.user.mention))
    
    @discord.app_commands.command()
    async def register(self, interaction: discord.Interaction, ign: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            minecraft_repo = MinecraftRepository(session)
            player_repo = PlayerRepository(session)
            
            service = MinecraftAccountService(minecraft_repo, player_repo)
            
            try:
                await service.link_account(
                    discord_user_id=str(interaction.user.id),
                    uuid=ign, # TODO: get uuid from mojang api
                    username=ign
                )
                await interaction.followup.send(f"✅ Successfully registered your Minecraft account `{ign}`!", ephemeral=True)
            except PlayerNotFound as e:
                await interaction.followup.send(f"🤔 Hmm. I don't know you, sorry. Try and say `/hello` in <#{CONFIG.register.hello_channel_id}> first.", ephemeral=True)
                return

async def setup(bot: commands.Bot):
    await bot.add_cog(RegisterCog(bot, SessionLocal))