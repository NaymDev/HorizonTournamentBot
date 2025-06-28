from atexit import unregister
from core.repositories.minecraft import MinecraftRepository
from core.repositories.players import PlayerRepository
from core.repositories.teams import TeamRepository
from core.repositories.tournaments import TournamentRepository
from db import models

TEAM_NAME_MAX_LENGTH = 20

class SignupError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

class TournamentNotFound(SignupError):
    pass

class SignupClosed(SignupError):
    pass

class TeamNameTooLong(SignupError):
    def __init__(self, max_length):
        super().__init__(f"Team name must be {max_length} characters or less.")
        self.max_length = max_length

class TeamNameTaken(SignupError):
    def __init__(self, team: models.Teams):
        super().__init__(f"Team name '{team.team_name}' is already taken.")
        self.team = team

class DuplicateTeamMemberError(SignupError):
    pass

class UnregisteredPlayersError(SignupError):
    def __init__(self, unregistered_ids: list[int]):
        super().__init__(f"Some players are not registered: {', '.join(map(str, unregistered_ids))}")
        self.unregistered_ids = unregistered_ids

class SignupService:
    def __init__(self, tournament_repo: TournamentRepository, team_repo: TeamRepository, player_repo: PlayerRepository, minecraft_repo: MinecraftRepository):
        self.tournament_repo: TournamentRepository = tournament_repo
        self.team_repo: TeamRepository = team_repo
        self.player_repo: PlayerRepository = player_repo
        self.minecraft_repo: MinecraftRepository = minecraft_repo
    
    async def signup_team(self, channel_id: str, team_name, members):
        tournament = await self.tournament_repo.get_tournament_for_signup_channel_id(channel_id)
            
        if not tournament:
            raise TournamentNotFound("Tournament not found in this channel")
        
        if tournament.status != models.TournamentStatus.signups:
            raise SignupClosed("Tournament signup is closed")
        
        if len(team_name) > TEAM_NAME_MAX_LENGTH:
            raise TeamNameTooLong(TEAM_NAME_MAX_LENGTH)
        
        existing_team = await self.team_repo.get_team_for_team_name(team_name)
        if existing_team:
            raise TeamNameTaken(existing_team)
        
        if len({m.id for m in members}) < len(members):
            raise DuplicateTeamMemberError("A team cannot have duplicate members")
        
        unregistered_ids = []
        for member in members:
            player = await self.player_repo.get_by_discord_id(member.id)
            if player is None:
                unregistered_ids.append(member.id)
                continue
            if await self.minecraft_repo.get_by_player_id(player.id) is None:
                unregistered_ids.append(member.id)
                continue
        
        if len(unregistered_ids) > 0:
            raise UnregisteredPlayersError(unregistered_ids)