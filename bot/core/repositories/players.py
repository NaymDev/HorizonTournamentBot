from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db import models

class PlayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_discord_id(self, discord_user_id: str) -> models.Players | None:
        """Retrieve a player by their Discord user ID."""
        try:
            stmt = select(models.Players).where(models.Players.discord_user_id == discord_user_id)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError:
            return None
    
    async def create_player(self, discord_user_id: str, username: str) -> models.Players | None:
        """Create a new player."""
        new_player = models.Players(discord_user_id=discord_user_id, username=username)
        try:
            self.session.add(new_player)
            await self.session.commit()
            await self.session.refresh(new_player)
            return new_player
        except SQLAlchemyError:
            await self.session.rollback()
            return None