import logging
from logging.handlers import RotatingFileHandler
import discord
from discord.ext import commands

from core.services.dm_notification import DmNotificationService, ModelTeamMembersGroup
from core.services.teamsubstitute import TeamSubstituteService
from core.repositories.tournaments import TournamentRepository
from db.session import SessionLocal
from core.repositories.members import MemberRepository
from core.repositories.players import PlayerRepository
from core.repositories.teams import TeamRepository
from db import models

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('cogs.teammanagemant.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class SignOffView(discord.ui.View):
    def __init__(self, team_id: str, tournament_id: str, cog):
        super().__init__(timeout=None)
        self.team_id = team_id
        self.tournament_id = tournament_id
        self.cog = cog

    @discord.ui.button(label="Sign Off", style=discord.ButtonStyle.danger, custom_id="sign_off_button")
    async def sign_off_button(self, interaction: discord.Interaction, button: discord.Button):
        async with self.cog.session_factory() as session:
            team_repo = TeamRepository(session)
            team = await team_repo.get_team_for_team_id(self.team_id)
            if team is None:
                await interaction.response.send_message("Team not found.", ephemeral=True)
                return
            
            if team.status == models.TeamStatus.rejected:
                await interaction.response.edit_message(
                    content=f"Team '{team.team_name}'  has already signed off.",
                    embed=None,
                    view=None
                )
                return
            
            old_status = team.status
            
            team.status = models.TeamStatus.rejected
            await session.commit()
            
            dm_notifications_service = DmNotificationService(self.cog.bot)
            
            if old_status == models.TeamStatus.accepted:
                service = TeamSubstituteService(team_repo, TournamentRepository(session), PlayerRepository(session), dm_notifications_service)
                service.update_teams_status_for_substitute(self.tournament_id)
            
            await dm_notifications_service.notify(
                await ModelTeamMembersGroup.create(team.members, self.player_repo),
                dm_notifications_service.message_cancelled,
                reason=f"A staff member has signed off the team '{team.team_name}' from the tournament `{self.tournament_id}`."
            )
                            
            # TODO: Move sign-off logic to service layer
            
            logger.info(f"Team {team.team_name} (ID: {self.team_id}) has signed off from tournament {self.tournament_id} by <@{interaction.user.id}>.")
            
            await interaction.response.edit_message(
                content=f"Team '{team.team_name}' has signed off from the tournament.",
                embed=None,
                view=None
            )

class TeamManageCog(commands.Cog):
    def __init__(self, bot: commands.Bot, session_factory):
        self.bot = bot
        self.session_factory = session_factory

    async def team_autocomplete(self, interaction: discord.Interaction, current: str):
        tournament_id = getattr(interaction.namespace, 'tournament', None)

        if tournament_id is None:
            return []
        
        async with self.session_factory() as session:
            team_repo = TeamRepository(session)
            teams: list[models.Teams] = await team_repo.get_all_teams_for_tournament(tournament_id)
                
        filtered_teams: list[models.Teams] = [team for team in teams if current.lower() in team.team_name.lower()]
        limited_teams: list[models.Teams] = filtered_teams[:25]

        return [
            discord.app_commands.Choice(name=team.team_name, value=str(team.id))
            for team in limited_teams
        ]
        
    async def tournament_autocomplete(self, interaction: discord.Interaction, current: str):
        async with self.session_factory() as session:
            tournament_repo = TournamentRepository(session)
            tournaments = await tournament_repo.get_all_tournaments()
            if tournaments is None:
                return []
                
        filtered_tournaments: list[models.Tournaments] = [tournament for tournament in tournaments if current.lower() in tournament.name.lower()]
        limited_tournaments: list[models.Tournaments] = filtered_tournaments[:25]

        return [
            discord.app_commands.Choice(name=tournament.name, value=str(tournament.id))
            for tournament in limited_tournaments
        ]
        
    @discord.app_commands.command()
    @discord.app_commands.autocomplete(team=team_autocomplete, tournament=tournament_autocomplete)
    async def info(self, interaction: discord.Interaction, tournament: str, team: str):
        team_id = team
        tournament_id = tournament
        
        if tournament_id is None or team_id is None:
            await interaction.response.send_message("Please provide a signup channel and team.", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True, ephemeral=True)
        async with self.session_factory() as session:
            team_repo = TeamRepository(session)
            team = await team_repo.get_team_for_team_id(team_id)
            if team is None:
                await interaction.followup.send("Team not found.", ephemeral=True)
                return
            
            player_repo = PlayerRepository(session)
            member_repo = MemberRepository(session)
            members_discord_ids = [int((await player_repo.get_by_id(member.player_id)).discord_user_id) for member in await member_repo.get_members_for_team(team_id)]
            
            
            status_str = {
                models.TeamStatus.pending: "Pending ⏳",
                models.TeamStatus.accepted: "Accepted 🟢",
                models.TeamStatus.substitute: "Substitute 🟠",
                models.TeamStatus.rejected: "Rejected 🔴"
            }.get(team.status, "Unknown")
            
            embed = discord.Embed(
                title=f"Team Information: {team.team_name}",
                description="\n".join([f"<:pr_enter:1370057653606154260> `👤` <@{user_id}>" for user_id in members_discord_ids]),
            ).set_footer(text=f"Status: {status_str}")

            if team.status in [models.TeamStatus.accepted, models.TeamStatus.substitute]:
                view = SignOffView(team_id=team_id, tournament_id=tournament_id, cog=self)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(TeamManageCog(bot, SessionLocal))