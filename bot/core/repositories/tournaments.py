from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import models

class TournamentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_tournament_for_signup_channel_id(self, channel_id: str) -> models.Tournaments | None:
        stmt = select(models.Tournaments).where(models.Tournaments.signup_channel_id == channel_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_tournament_by_id(self, tournament_id: int) -> models.Tournaments | None:
        stmt = select(models.Tournaments).where(models.Tournaments.id == tournament_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_tournaments(self) -> list[models.Tournaments] | None:
        stmt = select(models.Tournaments)
        result = await self.session.execute(stmt)
        tournaments = result.scalars().all()
        return tournaments if tournaments else None

    async def create_tournament(self, tournament_data: dict) -> models.Tournaments:
        tournament = models.Tournaments(**tournament_data)
        self.session.add(tournament)
        await self.session.commit()
        await self.session.refresh(tournament)
        return tournament
    
    async def set_status(self, tournament_id: str, status: models.TournamentStatus) -> None:
        tournament = await self.get_tournament_by_id(tournament_id)
        if tournament:
            tournament.status = status
            await self.session.commit()
        else:
            raise ValueError(f"Tournament with id {tournament_id} not found.")