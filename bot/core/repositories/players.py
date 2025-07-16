import datetime
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
    
    async def get_by_id(self, id: str) -> models.Players | None:
        """Retrieve a player by their ID."""
        try:
            stmt = select(models.Players).where(models.Players.id == id)
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
    
    async def is_player_banned(self, discord_user_id: str) -> bool:
        """Check if the player is banned by Discord user ID."""
        try:
            stmt = select(models.Bans).where(
                models.Bans.type == models.BanType.discord_user,
                models.Bans.discord_user_id == discord_user_id,
                (
                    models.Bans.expires_at == None
                    | (models.Bans.expires_at > datetime.datetime.now(datetime.timezone.utc))
                )
            )
            result = await self.session.execute(stmt)
            ban = result.scalars().first()
            return ban is not None
        except SQLAlchemyError:
            return False
    
    async def ban_discord_user(session, discord_user_id: str, reason: str, expires_at: datetime.datetime | None = None) -> bool:
        """Ban a player by their Discord user ID. Updates expired bans."""
        try:
            stmt = select(models.Bans).where(
                models.Bans.type == models.BanType.discord_user,
                models.Bans.discord_user_id == discord_user_id
            )
            result = await session.execute(stmt)
            existing_ban = result.scalars().first()
    
            now = datetime.datetime.now(datetime.timezone.utc)
    
            if existing_ban:
                # If ban is still active, don't re-ban
                if existing_ban.expires_at is None or existing_ban.expires_at > now:
                    return False
    
                # Update expired ban
                existing_ban.reason = reason
                existing_ban.expires_at = expires_at
                existing_ban.banned_at = now
                await session.commit()
                return True
    
            # No ban exists; create new one
            new_ban = models.Bans(
                type=models.BanType.discord_user,
                discord_user_id=discord_user_id,
                reason=reason,
                expires_at=expires_at
            )
            session.add(new_ban)
            await session.commit()
            return True
        except SQLAlchemyError:
            await session.rollback()
            return False
