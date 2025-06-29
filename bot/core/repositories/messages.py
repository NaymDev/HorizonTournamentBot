from typing import Optional
from sqlalchemy import select
from db import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

class MessageRepository:
    def __init__(self, session):
        self.session: AsyncSession = session
    
    async def get_all_signup_messages(self) -> list[models.Messages]:
        """Retrieve all signup messages."""
        try:
            stmt = select(models.Messages).where(models.Messages.purpose == "signup propose message")
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception:
            return []
    
    async def create_message(self, discord_message_id: str, discord_channel_id: str, team_id: int, purpose: str = "signup confirmation message") -> models.Messages | None:
        """Create a new message entry in the database."""
        new_message = models.Messages(
            discord_message_id=discord_message_id,
            discord_channel_id=discord_channel_id,
            team_id=team_id,
            purpose=purpose,
        )
        try:
            self.session.add(new_message)
            await self.session.commit()
            await self.session.refresh(new_message)
            return new_message
        except SQLAlchemyError:
            await self.session.rollback()
            return None
    
    async def get_by_discord_message_id(self, discord_message_id: str) -> Optional[models.Messages]:
        """Retrieve a message by its discord_message_id."""
        try:
            stmt = select(models.Messages).where(models.Messages.discord_message_id == discord_message_id)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception:
            return None