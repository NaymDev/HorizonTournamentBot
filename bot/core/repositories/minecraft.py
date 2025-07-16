import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


from db import models

class MinecraftRepository:
    def __init__(self, session):
        self.session: AsyncSession = session
    
    async def get_by_player_id(self, player_id: int) -> models.MinecraftAccounts | None:
        result = await self.session.execute(
            select(models.MinecraftAccounts).where(models.MinecraftAccounts.player_id == player_id)
        )
        return result.scalars().first()

    async def create_account(self, player_id: int, uuid: str, username: str) -> models.MinecraftAccounts:
        account = models.MinecraftAccounts(
            player_id=player_id,
            minecraft_uuid=uuid,
            minecraft_username=username
        )
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def update_account(self, player_id: int, uuid: str, username: str) -> models.MinecraftAccounts:
        account = await self.get_by_player_id(player_id)
        if not account:
            raise ValueError("Minecraft account not found")

        account.minecraft_uuid = uuid
        account.minecraft_username = username
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def log_history(self, player_id: int, uuid: str, username: str, change_type: str, note: str = None) -> models.MinecraftAccountHistory:
        if isinstance(change_type, str):
            try:
                change_type = models.MinecraftAccountHistoryChangeType[change_type]
            except KeyError:
                raise ValueError(f"Invalid change type: {change_type}")

        history = models.MinecraftAccountHistory(
            player_id=player_id,
            minecraft_uuid=uuid,
            minecraft_username=username,
            change_type=change_type,
            note=note
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history
    
    async def is_minecraft_account_banned(self, minecraft_uuid: str) -> bool:
        """Check if a Minecraft account is banned."""
        try:
            stmt = select(models.Bans).where(
                models.Bans.type == models.BanType.minecraft_account,
                models.Bans.minecraft_uuid == minecraft_uuid,
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
    
    async def ban_minecraft_account(session, minecraft_uuid: str, reason: str, expires_at: datetime.datetime | None = None) -> bool:
        """Ban a Minecraft account by UUID. Updates expired bans."""
        try:
            stmt = select(models.Bans).where(
                models.Bans.type == models.BanType.minecraft_account,
                models.Bans.minecraft_uuid == minecraft_uuid
            )
            result = await session.execute(stmt)
            existing_ban = result.scalars().first()

            now = datetime.datetime.now(datetime.timezone.utc)

            if existing_ban:
                if existing_ban.expires_at is None or existing_ban.expires_at > now:
                    return False

                existing_ban.reason = reason
                existing_ban.expires_at = expires_at
                existing_ban.banned_at = now
                await session.commit()
                return True

            new_ban = models.Bans(
                type=models.BanType.minecraft_account,
                minecraft_uuid=minecraft_uuid,
                reason=reason,
                expires_at=expires_at
            )
            session.add(new_ban)
            await session.commit()
            return True
        except SQLAlchemyError:
            await session.rollback()
            return False
