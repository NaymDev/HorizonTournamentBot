import datetime
from aiosqlite import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import models

class TeamRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_team_for_team_id(self, team_id: int) -> models.Teams | None:
        """Retrieve a team by its ID."""
        stmt = select(models.Teams).where(models.Teams.id == team_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_team_for_team_name(self, team_name: str) -> models.Teams | None:
        """Retrieve a team by its name."""
        stmt = select(models.Teams).where(models.Teams.team_name == team_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_status(self, team_id: int, status: str | models.TeamStatus):
        """Set the status of a team."""
        stmt = select(models.Teams).where(models.Teams.id == team_id)
        result = await self.session.execute(stmt)
        team = result.scalar_one_or_none()

        if team:
            team.status = status
            await self.session.commit()
    
    async def create_team(self, tournament_id: int, team_name: str, status: models.TeamStatus = models.TeamStatus.pending) -> models.Teams:
        """Create a new team under a tournament with initial status."""
        new_team = models.Teams(
            tournament_id=tournament_id,
            team_name=team_name,
            signup_time=datetime.datetime.now(datetime.timezone.utc),
            status=status
        )
        self.session.add(new_team)
        try:
            await self.session.commit()
            await self.session.refresh(new_team)
            return new_team
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"Team with name '{team_name}' already exists in tournament {tournament_id}.")
