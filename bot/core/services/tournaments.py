from uuid import uuid4
from challonge.client import ChallongeClient
from db.models import Tournaments
from core.repositories.tournaments import TournamentRepository
from sqlalchemy.exc import IntegrityError

class TournamentCreationError(Exception):
    pass

class DuplicateSignupChannelError(TournamentCreationError):
    def __init__(self, channel_id: str):
        super().__init__(f"Tournament with signup_channel_id '{channel_id}' already exists.")

class TournamentService:
    def __init__(self, tournament_repo: TournamentRepository, challonge_client: ChallongeClient):
        self.tournament_repo = tournament_repo
        self.challonge_client: ChallongeClient = challonge_client

    async def create_tournament(self, name: str, start_date, signup_channel_id: str, max_accepted_teams: int = 16) -> Tournaments:
        existing = await self.tournament_repo.get_tournament_for_signup_channel_id(signup_channel_id)
        if existing:
            raise DuplicateSignupChannelError(signup_channel_id)

        response = self.challonge_client.create_tournament(name, uuid4().hex)
        
        tournament_data = {
            "name": name,
            "start_date": start_date,
            "signup_channel_id": signup_channel_id,
            "max_accepted_teams": max_accepted_teams,
            "challonge_tournament_id": response["id"]
        }

        try:
            tournament = await self.tournament_repo.create_tournament(tournament_data)
            return tournament
        except IntegrityError as e:
            raise TournamentCreationError(f"Database error while creating tournament: {str(e)}")
