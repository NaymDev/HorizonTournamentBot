import discord
from discord.ext import commands

from core.repositories.tournaments import TournamentRepository
from db.session import SessionLocal
from core.repositories.members import MemberRepository
from core.repositories.players import PlayerRepository
from core.repositories.teams import TeamRepository
from db import models

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
            
            await interaction.followup.send(embed=discord.Embed(
                title=f"Team Information: {team.team_name}",
                description="\n".join([f"<:pr_enter:1370057653606154260> `👤` <@{user_id}>" for user_id in members_discord_ids]),
            ).set_footer(text=f"Status: {status_str}"), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(TeamManageCog(bot, SessionLocal))