import logging
import discord
from discord.ext import commands
from discord import app_commands

from bot.config import CONFIG
from bot.core.repositories.messages import MessageRepository
from bot.core.repositories.teams import TeamRepository
from bot.core.repositories.tournaments import TournamentRepository
from bot.core.services.signups import DuplicateTeamMemberError, SignupClosed, SignupService, TeamNameTaken, TeamNameTooLong, TournamentNotFound
from bot.core.services.teamreactions import TeamReactionService
from bot.db.session import SessionLocal

logger = logging.getLogger(__name__)

class SignupCog(commands.Cog):
    def __init__(self, bot, session_factory):
        self.bot: commands.Bot = bot
        self.session_factory = session_factory

    @commands.Cog.listener()
    async def on_ready(self):
        signup_channel = await self.bot.fetch_channel(CONFIG.signups.signup_channel_id)
        if signup_channel is None:
            logger.error(f"Signup channel with ID {CONFIG.signups.signup_channel_id} not found.")
            return
        
        async with self.session_factory() as session:
            team_repo = TeamRepository(session)
            message_repo = MessageRepository(session)
            service = TeamReactionService(team_repo, message_repo, None)
            
            signup_messages = message_repo.get_all_signup_messages()
            for msg in signup_messages:
                channel = self.bot.get_channel(msg.discord_channel_id)
                discord_message = await channel.fetch_message(int(msg.discord_message_id))
                
                if discord_message is None:
                    logger.warning(f"Signup Message with ID {msg.discord_message_id} not found in channel {msg.discord_channel_id}.")
                    continue

                service.handle_signup_reaction_check(discord_message)
    
    @app_commands.command(
        name="signup",
        description="Register your team",
    )
    @app_commands.describe(
        team_name="Your team’s name (≤20 chars)",
        p1="Team member 1 (must be verified)",
        p2="Team member 2 (must be verified)",
        p3="Team member 3 (must be verified)",
    )
    async def signup(
        self,
        interaction: discord.Interaction,
        team_name: str,
        p1: discord.Member,
        p2: discord.Member,
        p3: discord.Member,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            tournament_repo = TournamentRepository(session)
            team_repo = TeamRepository(session)
            
            service = SignupService(tournament_repo, team_repo)
            
            try:
                service.signup_team(    
                    channel_id=str(interaction.channel_id),
                    team_name=team_name,
                    members=[p1, p2, p3, interaction.user]
                )
            except TournamentNotFound:
                await interaction.followup.send("⚠️ No tournament is active in this channel. Please check the tournament channel.", ephemeral=True)
            except SignupClosed:
                await interaction.followup.send("🚫 Signup period is over. Please wait for the next tournament.", ephemeral=True)
            except TeamNameTooLong as e:
                await interaction.followup.send(f"⚠️ Team name must be {e.max_length} characters or less.", ephemeral=True)
            except TeamNameTaken as e:
                await interaction.followup.send(f"⚠️ Team name '{e.team.team_name}' is already taken. Please choose a different name.", ephemeral=True)    
            except DuplicateTeamMemberError:
                await interaction.followup.send("⚠️ A team cannot have duplicate members. Please ensure all members are unique.", ephemeral=True)
            

async def setup(bot):
    if CONFIG.signups.signup_channel_id is None:
        logger.warning("SignupCog not loaded: signup_channel_id is not set.")
        raise commands.ExtensionFailed("Signup channel ID not set in config.")
    await bot.add_cog(SignupCog(bot, SessionLocal))