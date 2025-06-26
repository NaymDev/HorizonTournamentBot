from sqlalchemy import select
from db import models
from sqlalchemy.ext.asyncio import AsyncSession

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