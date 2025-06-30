import logging
from logging.handlers import RotatingFileHandler
import random
import discord
from discord.ext import commands

from db.session import SessionLocal
from config import CONFIG
from core.repositories.players import PlayerRepository
from core.services.minecraft_account import AccountLinkError, DiscordTagMissmatch, MinecraftAccountNotFound, MinecraftAccountService, NoDiscordTagOnHypixel, PlayerNotFound
from core.repositories.minecraft import MinecraftRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('cogs.register.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    
    # Move the uuid eftching and checking logic into the business layer
    @discord.app_commands.command()
    async def register(self, interaction: discord.Interaction, ign: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            minecraft_repo = MinecraftRepository(session)
            player_repo = PlayerRepository(session)
            
            service = MinecraftAccountService(minecraft_repo, player_repo)
            
            try:
                await service.link_account(
                    discord_member=interaction.user,
                    username=ign
                )
                await interaction.followup.send(f"✅ Successfully registered your Minecraft account `{ign}`!", ephemeral=True)
            except PlayerNotFound:
                await interaction.followup.send(f"🤔 Hmm. I don't know you, sorry. Try and say `/hello` in <#{CONFIG.register.hello_channel_id}> first.", ephemeral=True)
            except MinecraftAccountNotFound as e:
                await interaction.followup.send(f"❌ The username `{e.username}` does not exist. Please check the spelling and try again.", ephemeral=True)
            except NoDiscordTagOnHypixel:
                await interaction.followup.send("🤔 Hmm. I can't find your Discord tag on Hypixel. Please ensure you have linked your Discord account on Hypixel.", ephemeral=True)
            except DiscordTagMissmatch:
                await interaction.followup.send("🤔 Hmm. The Discord tag from Hypixel does not match your Discord ID. Please ensure you have linked your Discord account on Hypixel correctly.", ephemeral=True)
            except AccountLinkError as e:
                logger.error(f"Error linking account for {interaction.user.name} ({interaction.user.id}): {str(e)}")
                await interaction.followup.send("❌ An error occurred while trying to register your account. If this keeps happening please contact our staff team.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send("❌ An unexpected error occurred while trying to register your account. Please try again later.", ephemeral=True)
                raise e
    
    @discord.app_commands.command()
    @discord.app_commands.default_permissions(administrator=True)
    async def register_other(self, interaction: discord.Interaction, discord_member: discord.Member, ign: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            player_repo = PlayerRepository(session)
            if not (await player_repo.get_by_discord_id(str(discord_member.id))):
                await player_repo.create_player(
                    discord_member.id,
                    discord_member.name
                )
        
            minecraft_repo = MinecraftRepository(session)
            
            service = MinecraftAccountService(minecraft_repo, player_repo)
            
            try:
                await service.link_account(
                    discord_member=discord_member,
                    username=ign
                )
                await interaction.followup.send(f"✅ Successfully registered your Minecraft account `{ign}`!", ephemeral=True)
            except PlayerNotFound:
                await interaction.followup.send(f"🤔 Hmm. I don't know you, sorry. Try and say `/hello` in <#{CONFIG.register.hello_channel_id}> first.", ephemeral=True)
            except MinecraftAccountNotFound as e:
                await interaction.followup.send(f"❌ The username `{e.username}` does not exist. Please check the spelling and try again.", ephemeral=True)
            except NoDiscordTagOnHypixel:
                await interaction.followup.send("🤔 Hmm. I can't find your Discord tag on Hypixel. Please ensure you have linked your Discord account on Hypixel.", ephemeral=True)
            except DiscordTagMissmatch:
                await interaction.followup.send("🤔 Hmm. The Discord tag from Hypixel does not match your Discord ID. Please ensure you have linked your Discord account on Hypixel correctly.", ephemeral=True)
            except AccountLinkError as e:
                logger.error(f"Error linking account for {discord_member.name} ({discord_member.id}): {str(e)}")
                await interaction.followup.send("❌ An error occurred while trying to register your account. If this keeps happening please contact our staff team.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send("❌ An unexpected error occurred while trying to register your account. Please try again later.", ephemeral=True)
                raise e
    
    @discord.app_commands.command(name="update")
    @discord.app_commands.guild_only()
    @discord.app_commands.checks.cooldown(1, 180)
    async def update(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            minecraft_repo = MinecraftRepository(session)
            player_repo = PlayerRepository(session)
            
            service = MinecraftAccountService(minecraft_repo, player_repo)
            
            try:
                await service.update_discord_nick(interaction.user)
                await interaction.followup.send("✅ Successfully updated your Discord nickname!", ephemeral=True)
            except PlayerNotFound:
                await interaction.followup.send(f"🤔 Hmm. I don't know you, sorry. Try and say `/hello` in <#{CONFIG.register.hello_channel_id}> first.", ephemeral=True)
            
    @update.error
    async def on_update_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)
            
async def setup(bot: commands.Bot):
    await bot.add_cog(RegisterCog(bot, SessionLocal))