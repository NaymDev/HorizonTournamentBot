from abc import ABC, abstractmethod
import asyncio
from typing import Awaitable, Callable
import discord
from discord.ext import commands

from core.repositories.members import MemberRepository
from core.repositories.players import PlayerRepository
from db import models

class MessageTargetGroupe(ABC):
    @abstractmethod
    def get_target_discord_ids(self) -> list[int]:
        pass

class DiscordGroup(MessageTargetGroupe):
    def __init__(self, discord_ids: list[int]):
        self._discord_ids = discord_ids

    def get_target_discord_ids(self) -> list[int]:
        return self._discord_ids

class ModelTeamMembersGroup(MessageTargetGroupe):
    def __init__(self, discord_ids):
        self._discord_ids = discord_ids

    @classmethod
    async def create(cls, team_members: list[models.TeamMembers], player_repo: PlayerRepository):
        async def get_discord_id(member):
            player = await player_repo.get_by_id(member.player_id)
            return int(player.discord_user_id)
    
        discord_ids = await asyncio.gather(*(get_discord_id(member) for member in team_members))
        return cls(discord_ids=discord_ids)
    
    def get_target_discord_ids(self) -> list[int]:
        return self._discord_ids
    
class DmNotificationService:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def message_accept(self, channel: discord.DMChannel):
        await channel.send()
    
    # Called when a team gets accepted but only as a substitute because the tournament has reached the maxmimum amount of accepted teams
    async def message_accept_as_substitute(self, channel: discord.DMChannel):
        await channel.send()
    
    # Called when a substitute team gets accepted (eg because another team cancels and theres a new slot availabel)
    async def message_substitue_accept(self, channel: discord.DMChannel):
        await channel.send()
    
    async def message_rejected_by(self, channel: discord.DMChannel, rejected_by: list[discord.Member]):
        await channel.send()
    
    async def message_cancelled(self, channel: discord.DMChannel, reason: str):
        await channel.send()
    
    async def notify(self, target: MessageTargetGroupe, message_send_func: Callable[[discord.DMChannel], Awaitable[None]], **kwargs):
        for discord_id in target.get_target_discord_ids():
            user = self.bot.get_user(discord_id) or await self.bot.fetch_user(discord_id)
            try:
                dm_channel = user.dm_channel or await user.create_dm()
                self.bot.loop.create_task(message_send_func(dm_channel, kwargs))
            except discord.Forbidden:
                print(f"Could not send DM to {user.name} (ID: {discord_id}). They might have DMs disabled.")
            except Exception as e:
                print(f"An error occurred while sending DM to {user.name} (ID: {discord_id}): {e}")