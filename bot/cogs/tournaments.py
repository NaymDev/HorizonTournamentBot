from logging.handlers import RotatingFileHandler
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import logging

from db.session import SessionLocal
from core.repositories.tournaments import TournamentRepository
from core.services.tournaments import TournamentService, TournamentCreationError, DuplicateSignupChannelError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('cogs.tournaments.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class TournamentCog(commands.Cog):
    def __init__(self, bot: commands.Bot, session_factory):
        self.bot = bot
        self.session_factory = session_factory

    @app_commands.command(name="create_tournament", description="Create a new tournament (Admin only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        name="The name of the tournament.",
        start_date="The start date and time (format: YYYY-MM-DD HH:MM, in UTC).",
        signup_channel="The Discord text channel where teams will sign up.",
        max_accepted_teams="Maximum number of teams that can join the tournament (default: 16)."
    )
    async def create_tournament(
        self,
        interaction: discord.Interaction,
        name: str,
        start_date: str,
        signup_channel: discord.TextChannel,
        max_accepted_teams: int = 16,
    ):
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M")
                start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                await interaction.followup.send("❌ Invalid date format. Please use `YYYY-MM-DD HH:MM`.", ephemeral=True)
                return

            async with self.session_factory() as session:
                tournament_repo = TournamentRepository(session)
                tournament_service = TournamentService(tournament_repo)

                tournament = await tournament_service.create_tournament(
                    name=name,
                    start_date=start_dt,
                    signup_channel_id=str(signup_channel.id),
                    max_accepted_teams=max_accepted_teams
                )

                await interaction.followup.send(
                    f"✅ Tournament **{tournament.name}** created!\n"
                    f"• Start Date: <t:{int(start_dt.timestamp())}:F>\n"
                    f"• Signup Channel: {signup_channel.mention}\n"
                    f"• Max Teams: {max_accepted_teams}",
                    ephemeral=True
                )

        except DuplicateSignupChannelError:
            await interaction.followup.send(f"❌ A tournament already uses that signup channel ({signup_channel.jump_url}).", ephemeral=True)
        except TournamentCreationError as e:
            logger.exception("Tournament creation failed")
            await interaction.followup.send(f"❌ Failed to create tournament: {str(e)}", ephemeral=True)
        except Exception as e:
            logger.exception("Unexpected error during tournament creation")
            await interaction.followup.send("❌ Unexpected error while creating the tournament.", ephemeral=True)
            raise e

async def setup(bot: commands.Bot):
    await bot.add_cog(TournamentCog(bot, SessionLocal))