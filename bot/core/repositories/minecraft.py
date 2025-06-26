from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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