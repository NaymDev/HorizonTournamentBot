from aiosqlite import IntegrityError
from sqlalchemy import and_, select
from db import models
from sqlalchemy.ext.asyncio import AsyncSession


class MemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_members_for_team(self, team_id: int) -> list[models.TeamMembers]:
        stmt = select(models.TeamMembers).where(models.TeamMembers.team_id == team_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_member_to_team(self, team_id: int, player_id: int, role: models.PlayerRole = models.PlayerRole.member) -> models.TeamMembers:
        """Add a player as a member to a team."""
        new_member = models.TeamMembers(
            team_id=team_id,
            player_id=player_id,
            role=role,
            accepted=False,
            responded=False,
            response=None
        )
        self.session.add(new_member)
        try:
            await self.session.commit()
            await self.session.refresh(new_member)
            return new_member
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"Player {player_id} is already a member of team {team_id}.")
    
    async def is_player_in_tournament_non_rejected_team(self, player_id: int, tournament_id: int) -> bool:
        """
        Check if a player is part of a team in the given tournament where
        the team's status is NOT rejected.
        """
        stmt = (
            select(models.TeamMembers)
            .join(models.Teams, models.TeamMembers.team_id == models.Teams.id)
            .where(
                and_(
                    models.TeamMembers.player_id == player_id,
                    models.Teams.tournament_id == tournament_id,
                    models.Teams.status != models.TeamStatus.rejected
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None