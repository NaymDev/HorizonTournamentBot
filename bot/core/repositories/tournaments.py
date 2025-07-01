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
    
    async def get_all_tournaments(self) -> list[models.Tournaments] | None:
        stmt = select(models.Tournaments)
        result = await self.session.execute(stmt)
        tournaments = result.scalars().all()
        return tournaments if tournaments else None
