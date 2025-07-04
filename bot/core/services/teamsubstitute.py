import logging
from logging.handlers import RotatingFileHandler
from core.repositories.players import PlayerRepository
from core.services.dm_notification import DmNotificationService, ModelTeamMembersGroup
from core.repositories.tournaments import TournamentRepository
from db import models
from core.repositories.teams import TeamRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('services.teamsubstitute.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class TeamSubstituteService:
    def __init__(self, team_repo: TeamRepository, tournament_repo: TournamentRepository, player_repo: PlayerRepository, dm_notifications_service: DmNotificationService):
        self.team_repo: TeamRepository = team_repo
        self.tournament_repo: TournamentRepository = tournament_repo
        self.player_repo: PlayerRepository = player_repo
        self.dm_notifications_service: DmNotificationService = dm_notifications_service
    
    async def update_teams_status_for_substitute(self, tournament_id: int):
        """
        Update the status of all teams in the tournament to ensure that the first team to get accepted as a substitute
        gets accepted and notified.
        """
        logger.debug(f"Starting update_teams_status_for_substitute for tournament_id={tournament_id}")
        
        tournament = await self.tournament_repo.get_tournament_for_signup_channel_id(tournament_id)
        if not tournament:
            logger.warning(f"Tournament not found for id={tournament_id}")
            return
        
        accepted_count = await self.team_repo.get_accepted_team_count(tournament_id)
        logger.debug(f"Accepted teams count: {accepted_count} / max allowed: {tournament.max_accepted_teams}")
        if accepted_count >= tournament.max_accepted_teams:
            logger.info(f"Max accepted teams reached for tournament_id={tournament_id}. No substitutes accepted.")
            return
        
        while True:
            team = await self.team_repo.get_earliest_substitute_team(tournament_id)
            if team is None:
                logger.info(f"No more substitute teams to process for tournament_id={tournament_id}")
                return
            
            logger.info(f"Accepting substitute team_id={team.id} for tournament_id={tournament_id}")
            self.team_repo.set_status(team.id, models.TeamStatus.accepted)
            
            await self.dm_notifications_service.notify(
                await ModelTeamMembersGroup.create(team.members, self.player_repo),
                self.dm_notifications_service.message_substitue_accept
            )