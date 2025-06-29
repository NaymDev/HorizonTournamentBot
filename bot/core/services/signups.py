from typing import Awaitable, Callable

import discord
from core.repositories.members import MemberRepository
from core.repositories.messages import MessageRepository
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

class PlayerAlreadyInATeam(SignupError):
    def __init__(self, player: int):
        super().__init__(f"Player {player} is already in a team.")
        self.player = player

class SignupService:
    def __init__(self, tournament_repo: TournamentRepository, team_repo: TeamRepository, player_repo: PlayerRepository, minecraft_repo: MinecraftRepository, message_repo: MessageRepository, member_repo: MemberRepository):
        self.tournament_repo: TournamentRepository = tournament_repo
        self.team_repo: TeamRepository = team_repo
        self.player_repo: PlayerRepository = player_repo
        self.minecraft_repo: MinecraftRepository = minecraft_repo
        self.message_repo: MessageRepository = message_repo
        self.member_repo: MemberRepository = member_repo
    
    async def signup_team(self, channel_id: str, team_name, members, message_send: Callable[[str], Awaitable[discord.Message]]) -> discord.Message:
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
            if await self.member_repo.is_player_in_tournament_non_rejected_team(player.id, tournament.id):
                raise PlayerAlreadyInATeam(player.discord_user_id)
        
        if len(unregistered_ids) > 0:
            raise UnregisteredPlayersError(unregistered_ids)
        
        team = await self.team_repo.create_team(tournament_id=tournament.id, team_name=team_name)

        for member in members:
            player = await self.player_repo.get_by_discord_id(member.id)
            await self.member_repo.add_member_to_team(team_id=team.id, player_id=player.id)

        message = await message_send(team.id)
        await self.message_repo.create_message(
            discord_message_id=str(message.id),
            discord_channel_id=str(message.channel.id),
            team_id=team.id,
            purpose="signup propose message"
        )
        
        return message